use clap::{Parser, Subcommand};
use anyhow::{Context, Result};
use oxigraph::store::Store;
use oxigraph::sparql::{Query, QueryResults};
use oxigraph::model::Term;
use serde::Serialize;
use std::fs;
use std::path::{Path, PathBuf};
use tera::{Tera, Context as TeraContext};
use walkdir::WalkDir;

#[derive(Parser)]
#[command(name = "ggen")]
#[command(about = "Ontology compiler - transforms RDF to typed code", long_about = None)]
#[command(version = "5.0.0")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Compile ontology to code (sync)
    Sync {
        /// Source ontology directory
        #[arg(long)]
        from: Option<String>,

        /// Target output directory
        #[arg(long)]
        to: Option<String>,

        /// Sync mode: full, incremental, verify
        #[arg(long, default_value = "full")]
        mode: String,

        /// Preview changes without writing
        #[arg(long)]
        dry_run: bool,

        /// Override conflicts
        #[arg(long)]
        force: bool,

        /// Verbose output
        #[arg(long, short)]
        verbose: bool,
    },

    /// Display version
    Version,
}

#[derive(Debug, Serialize)]
struct OntologyClass {
    name: String,
    comment: String,
    properties: Vec<Property>,
}

#[derive(Debug, Serialize)]
struct Property {
    name: String,
    comment: String,
    rust_type: String,
    python_type: String,
    typescript_type: String,
    optional: bool,
}

fn load_ontology(ontology_dir: &Path, verbose: bool) -> Result<Store> {
    let store = Store::new()?;

    if verbose {
        println!("📖 Loading ontologies from: {}", ontology_dir.display());
    }

    // Find all .ttl files in the ontology directory
    for entry in WalkDir::new(ontology_dir)
        .follow_links(true)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| e.path().extension().map_or(false, |ext| ext == "ttl"))
    {
        let path = entry.path();
        if verbose {
            println!("  - Loading: {}", path.display());
        }

        let content = fs::read_to_string(path)
            .with_context(|| format!("Failed to read {}", path.display()))?;

        store.load_from_reader(
            oxigraph::io::RdfFormat::Turtle,
            content.as_bytes(),
        )?;
    }

    Ok(store)
}

fn extract_classes(store: &Store, verbose: bool) -> Result<Vec<OntologyClass>> {
    if verbose {
        println!("\n🔍 Extracting classes from ontology...");
    }

    // SPARQL query to find all classes
    let query_str = r#"
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>

        SELECT DISTINCT ?class ?label ?comment
        WHERE {
            ?class a ?classType .
            VALUES ?classType { rdfs:Class owl:Class }
            OPTIONAL { ?class rdfs:label ?label }
            OPTIONAL { ?class rdfs:comment ?comment }
        }
        ORDER BY ?class
    "#;

    let query = Query::parse(query_str, None)?;
    let results = store.query(query)?;
    let mut classes = Vec::new();

    if let QueryResults::Solutions(solutions) = results {
        for solution in solutions {
            let solution = solution?;

            if let Some(class_term) = solution.get("class") {
                // Get the IRI string
                let class_iri = match class_term {
                    Term::NamedNode(node) => node.as_str(),
                    _ => continue,
                };

                // Skip RDF/RDFS/OWL built-in classes
                if class_iri.contains("www.w3.org") {
                    continue;
                }

                // Extract simple class name from IRI
                let class_name = class_iri
                    .split(&['#', '/'][..])
                    .last()
                    .unwrap_or("Unknown");

                let comment = solution.get("comment")
                    .map(|v| v.to_string().trim_matches('"').to_string())
                    .unwrap_or_default();

                if verbose {
                    println!("  ✓ Found class: {}", class_name);
                }

                // Extract properties for this class
                let properties = extract_properties(store, class_iri, verbose)?;

                classes.push(OntologyClass {
                    name: class_name.to_string(),
                    comment,
                    properties,
                });
            }
        }
    }

    Ok(classes)
}

fn extract_properties(store: &Store, class_iri: &str, _verbose: bool) -> Result<Vec<Property>> {
    let query_str = format!(r#"
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

        SELECT DISTINCT ?property ?label ?comment ?range
        WHERE {{
            ?property rdfs:domain <{}> .
            OPTIONAL {{ ?property rdfs:label ?label }}
            OPTIONAL {{ ?property rdfs:comment ?comment }}
            OPTIONAL {{ ?property rdfs:range ?range }}
        }}
        ORDER BY ?property
    "#, class_iri);

    let query = Query::parse(&query_str, None)?;
    let results = store.query(query)?;
    let mut properties = Vec::new();

    if let QueryResults::Solutions(solutions) = results {
        for solution in solutions {
            let solution = solution?;

            if let Some(prop_term) = solution.get("property") {
                let prop_uri = prop_term.to_string();
                let prop_name = prop_uri
                    .split(&['#', '/'][..])
                    .last()
                    .unwrap_or("unknown")
                    .trim_matches('>');

                let comment = solution.get("comment")
                    .map(|v| v.to_string().trim_matches('"').to_string())
                    .unwrap_or_default();

                let range = solution.get("range")
                    .map(|v| v.to_string())
                    .unwrap_or_else(|| "xsd:string".to_string());

                // Map XSD types to target language types
                let (rust_type, python_type, typescript_type) = map_xsd_type(&range);

                properties.push(Property {
                    name: prop_name.to_string(),
                    comment,
                    rust_type,
                    python_type,
                    typescript_type,
                    optional: false,
                });
            }
        }
    }

    Ok(properties)
}

fn map_xsd_type(xsd_type: &str) -> (String, String, String) {
    if xsd_type.contains("string") {
        ("String".to_string(), "str".to_string(), "string".to_string())
    } else if xsd_type.contains("integer") || xsd_type.contains("int") {
        ("i64".to_string(), "int".to_string(), "number".to_string())
    } else if xsd_type.contains("boolean") {
        ("bool".to_string(), "bool".to_string(), "boolean".to_string())
    } else if xsd_type.contains("dateTime") {
        ("DateTime<Utc>".to_string(), "datetime".to_string(), "Date".to_string())
    } else if xsd_type.contains("decimal") || xsd_type.contains("float") {
        ("f64".to_string(), "float".to_string(), "number".to_string())
    } else {
        // Custom class type
        let type_name = xsd_type
            .split(&['#', '/'][..])
            .last()
            .unwrap_or("String")
            .trim_matches('>');
        (type_name.to_string(), type_name.to_string(), type_name.to_string())
    }
}

fn render_templates(
    classes: &[OntologyClass],
    templates_dir: &Path,
    output_dir: &Path,
    dry_run: bool,
    verbose: bool,
) -> Result<()> {
    if verbose {
        println!("\n🎨 Rendering templates from: {}", templates_dir.display());
    }

    // Initialize Tera with all template files
    let template_pattern = format!("{}/**/*.tera", templates_dir.display());
    let mut tera = Tera::new(&template_pattern)
        .with_context(|| format!("Failed to load templates from {}", templates_dir.display()))?;

    // Disable auto-escaping for code generation
    tera.autoescape_on(vec![]);

    // Prepare context
    let mut context = TeraContext::new();
    context.insert("classes", classes);
    context.insert("enumerations", &Vec::<String>::new()); // Empty for now
    context.insert("ontology", "specify-domain.ttl");

    // Create output directory
    if !dry_run {
        fs::create_dir_all(output_dir)
            .with_context(|| format!("Failed to create output directory: {}", output_dir.display()))?;
    }

    // Render each template
    for template_name in tera.get_template_names() {
        if verbose {
            println!("  - Rendering: {}", template_name);
        }

        let output = tera.render(template_name, &context)
            .with_context(|| format!("Failed to render template: {}", template_name))?;

        // Determine output file name (remove .tera extension, add appropriate extension)
        let temp_path = PathBuf::from(template_name);
        let output_file = temp_path
            .file_stem()
            .unwrap()
            .to_str()
            .unwrap();

        let output_path = output_dir.join(output_file);

        if dry_run {
            println!("\n--- {} ---", output_path.display());
            println!("{}", output.lines().take(20).collect::<Vec<_>>().join("\n"));
            if output.lines().count() > 20 {
                println!("... ({} more lines)", output.lines().count() - 20);
            }
        } else {
            fs::write(&output_path, output)
                .with_context(|| format!("Failed to write {}", output_path.display()))?;
            if verbose {
                println!("    ✓ Generated: {}", output_path.display());
            }
        }
    }

    Ok(())
}

fn main() -> Result<()> {
    let cli = Cli::parse();

    match cli.command {
        Commands::Sync { from, to, mode, dry_run, force: _, verbose } => {
            let ontology_dir = PathBuf::from(from.unwrap_or_else(|| "schema".to_string()));
            let output_dir = PathBuf::from(to.unwrap_or_else(|| "src/generated".to_string()));

            println!("🚀 ggen ontology compiler");
            println!("   Source: {}", ontology_dir.display());
            println!("   Output: {}", output_dir.display());
            println!("   Mode: {}", mode);
            if dry_run {
                println!("   🔍 DRY RUN - no files will be written");
            }
            println!();

            // Load ontology
            let store = load_ontology(&ontology_dir, verbose)?;

            // Extract classes and properties
            let classes = extract_classes(&store, verbose)?;

            if verbose {
                println!("\n📊 Extracted {} classes", classes.len());
            }

            // Find templates directory
            let templates_dir = PathBuf::from("templates/ggen");
            if !templates_dir.exists() {
                anyhow::bail!("Templates directory not found: {}", templates_dir.display());
            }

            // Render templates
            render_templates(&classes, &templates_dir, &output_dir, dry_run, verbose)?;

            if !dry_run {
                println!("\n✅ Compilation complete! Generated code written to: {}", output_dir.display());
            } else {
                println!("\n✅ Dry run complete! Use without --dry-run to write files.");
            }

            Ok(())
        }
        Commands::Version => {
            println!("ggen 5.0.0");
            println!("Ontology compiler for spec-driven development");
            Ok(())
        }
    }
}
