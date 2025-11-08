// Jenkins Pipeline for Codebase Analysis
//
// This Jenkinsfile runs the Reverse Engineering & Modernization analysis
// and publishes results.
//
// Usage:
//   1. Create a new Pipeline job in Jenkins
//   2. Point to this Jenkinsfile or copy content to Pipeline script
//   3. Configure parameters as needed

pipeline {
    agent {
        label 'linux'  // Or any agent with Python and Git
    }

    parameters {
        choice(
            name: 'ANALYSIS_DEPTH',
            choices: ['STANDARD', 'QUICK', 'COMPREHENSIVE'],
            description: 'Analysis depth level'
        )
        booleanParam(
            name: 'FAIL_ON_VULNERABILITIES',
            defaultValue: true,
            description: 'Fail build if vulnerable dependencies found'
        )
    }

    environment {
        PYTHON_VERSION = '3.11'
        SPEC_KIT_DIR = '/tmp/spec-kit'
    }

    triggers {
        // Run weekly on Mondays at 9 AM
        cron('0 9 * * 1')
    }

    stages {
        stage('Setup') {
            steps {
                script {
                    echo "Setting up analysis environment"
                }

                // Install tools
                sh '''
                    # Install cloc if not available
                    if ! command -v cloc &> /dev/null; then
                        sudo apt-get update
                        sudo apt-get install -y cloc || echo "Could not install cloc"
                    fi

                    # Install Python tools
                    pip3 install --user pip-audit || echo "Could not install pip-audit"
                '''

                // Clone spec-kit-smart
                sh '''
                    rm -rf ${SPEC_KIT_DIR}
                    git clone https://github.com/veerabhadra-ponna/spec-kit-smart.git ${SPEC_KIT_DIR}
                    chmod +x ${SPEC_KIT_DIR}/scripts/bash/analyze-project.sh
                '''
            }
        }

        stage('Analyze Codebase') {
            steps {
                script {
                    echo "Running codebase analysis with depth: ${params.ANALYSIS_DEPTH}"
                }

                sh '''
                    ${SPEC_KIT_DIR}/scripts/bash/analyze-project.sh \
                        ${WORKSPACE} \
                        --depth ${ANALYSIS_DEPTH} \
                        --output analysis-results
                '''
            }
        }

        stage('Process Results') {
            steps {
                script {
                    // Read metrics
                    if (fileExists('analysis-results/metrics-summary.json')) {
                        def metrics = readJSON file: 'analysis-results/metrics-summary.json'

                        echo "=== Analysis Results ==="
                        echo "Inline Upgrade Score: ${metrics.feasibility.inline_upgrade_score}/100"
                        echo "Greenfield Rewrite Score: ${metrics.feasibility.greenfield_rewrite_score}/100"
                        echo "Recommendation: ${metrics.feasibility.recommendation}"
                        echo "Vulnerable Dependencies: ${metrics.dependencies.vulnerable}"
                        echo "Outdated Dependencies: ${metrics.dependencies.outdated}"

                        // Set build description
                        currentBuild.description = "Recommendation: ${metrics.feasibility.recommendation}"

                        // Store metrics as build data
                        env.VULNERABLE_COUNT = metrics.dependencies.vulnerable
                        env.INLINE_SCORE = metrics.feasibility.inline_upgrade_score
                        env.RECOMMENDATION = metrics.feasibility.recommendation
                    }
                }
            }
        }

        stage('Publish Reports') {
            steps {
                // Archive artifacts
                archiveArtifacts artifacts: 'analysis-results/**/*', fingerprint: true

                // Publish HTML reports if plugin available
                script {
                    if (fileExists('analysis-results/analysis-report.md')) {
                        // Convert markdown to HTML (requires pandoc)
                        sh '''
                            if command -v pandoc &> /dev/null; then
                                pandoc analysis-results/analysis-report.md -o analysis-results/analysis-report.html
                            fi
                        '''

                        // Publish HTML if available
                        if (fileExists('analysis-results/analysis-report.html')) {
                            publishHTML(target: [
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'analysis-results',
                                reportFiles: 'analysis-report.html',
                                reportName: 'Codebase Analysis Report'
                            ])
                        }
                    }
                }
            }
        }

        stage('Security Gate') {
            when {
                expression { params.FAIL_ON_VULNERABILITIES == true }
            }
            steps {
                script {
                    if (env.VULNERABLE_COUNT && env.VULNERABLE_COUNT.toInteger() > 0) {
                        error("Build failed: ${env.VULNERABLE_COUNT} vulnerable dependencies detected!")
                    }
                }
            }
        }
    }

    post {
        always {
            // Clean up
            cleanWs(
                deleteDirs: true,
                patterns: [[pattern: 'analysis-results/**', type: 'INCLUDE']]
            )
        }

        success {
            script {
                echo "Analysis completed successfully"

                // Send notification (requires appropriate plugin)
                // emailext (
                //     subject: "Codebase Analysis: ${currentBuild.result}",
                //     body: "Recommendation: ${env.RECOMMENDATION}\nView reports: ${env.BUILD_URL}",
                //     to: "team@example.com"
                // )
            }
        }

        failure {
            script {
                echo "Analysis failed or found critical issues"

                // Send alert
                // emailext (
                //     subject: "Codebase Analysis FAILED: ${currentBuild.result}",
                //     body: "Vulnerable dependencies: ${env.VULNERABLE_COUNT}\nView logs: ${env.BUILD_URL}",
                //     to: "team@example.com"
                // )
            }
        }
    }
}
