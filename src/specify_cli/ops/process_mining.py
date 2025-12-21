"""
specify_cli.ops.process_mining - Business logic for process mining operations

This module contains the pure business logic for process mining operations,
separated from the CLI layer for better testability and reusability.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional


def load_event_log(
    file_path: Path,
    case_id: str = "case:concept:name",
    activity: str = "concept:name",
    timestamp: str = "time:timestamp",
):
    """
    Load an event log from file (XES or CSV).

    Args:
        file_path: Path to XES or CSV file
        case_id: Column name for case ID (CSV only)
        activity: Column name for activity (CSV only)
        timestamp: Column name for timestamp (CSV only)

    Returns:
        EventLog object

    Raises:
        ValueError: If file format is unsupported
        FileNotFoundError: If file doesn't exist
    """
    import pm4py

    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    suffix = file_path.suffix.lower()

    if suffix == ".xes":
        return pm4py.read_xes(str(file_path))
    elif suffix == ".csv":
        import pandas as pd

        df = pd.read_csv(file_path)
        # Format as event log
        df = pm4py.format_dataframe(
            df, case_id=case_id, activity_key=activity, timestamp_key=timestamp
        )
        return pm4py.convert_to_event_log(df)
    else:
        raise ValueError(f"Unsupported file format: {suffix}. Use .xes or .csv")


def save_model(model: Any, output_path: Path, model_type: str = "petri") -> None:
    """
    Save a process model to file.

    Args:
        model: Process model (Petri net tuple, BPMN, or process tree)
        output_path: Output file path
        model_type: Type of model ('petri', 'bpmn', 'tree')

    Raises:
        ValueError: If output format is unsupported
    """
    import pm4py

    suffix = output_path.suffix.lower()

    if model_type == "petri":
        net, im, fm = model
        if suffix == ".pnml":
            pm4py.write_pnml(net, im, fm, str(output_path))
        elif suffix in [".png", ".svg"]:
            pm4py.save_vis_petri_net(net, im, fm, str(output_path))
        else:
            raise ValueError(f"Unsupported output format for Petri net: {suffix}")
    elif model_type == "bpmn":
        if suffix == ".bpmn":
            pm4py.write_bpmn(model, str(output_path))
        elif suffix in [".png", ".svg"]:
            pm4py.save_vis_bpmn(model, str(output_path))
        else:
            raise ValueError(f"Unsupported output format for BPMN: {suffix}")
    elif model_type == "tree":
        if suffix in [".png", ".svg"]:
            pm4py.save_vis_process_tree(model, str(output_path))
        else:
            raise ValueError(f"Unsupported output format for process tree: {suffix}")


def discover_process_model(
    log,
    algorithm: str = "inductive",
    noise_threshold: float = 0.0,
) -> Tuple[Any, str]:
    """
    Discover a process model from an event log.

    Args:
        log: EventLog object
        algorithm: Discovery algorithm (alpha, alpha_plus, heuristic, inductive, ilp)
        noise_threshold: Noise threshold for inductive miner (0.0-1.0)

    Returns:
        Tuple of (model, model_type)

    Raises:
        ValueError: If algorithm is unknown
    """
    import pm4py

    if algorithm == "alpha":
        net, im, fm = pm4py.discover_petri_net_alpha(log)
        return (net, im, fm), "petri"
    elif algorithm == "alpha_plus":
        net, im, fm = pm4py.discover_petri_net_alpha_plus(log)
        return (net, im, fm), "petri"
    elif algorithm == "heuristic":
        net, im, fm = pm4py.discover_petri_net_heuristics(log)
        return (net, im, fm), "petri"
    elif algorithm == "inductive":
        net, im, fm = pm4py.discover_petri_net_inductive(
            log, noise_threshold=noise_threshold
        )
        return (net, im, fm), "petri"
    elif algorithm == "ilp":
        net, im, fm = pm4py.discover_petri_net_ilp(log)
        return (net, im, fm), "petri"
    else:
        raise ValueError(f"Unknown discovery algorithm: {algorithm}")


def conform_trace(
    log,
    model_file: Path,
    method: str = "token",
) -> Dict[str, Any]:
    """
    Perform conformance checking between an event log and a process model.

    Args:
        log: EventLog object
        model_file: Path to PNML or BPMN model file
        method: Conformance method ('token' or 'alignment')

    Returns:
        Dictionary with conformance results (fitness, precision, F1-score, etc.)

    Raises:
        ValueError: If method is unknown or model file is invalid
    """
    import pm4py

    if not model_file.exists():
        raise FileNotFoundError(f"Model file not found: {model_file}")

    # Load model
    suffix = model_file.suffix.lower()
    if suffix == ".pnml":
        net, im, fm = pm4py.read_pnml(str(model_file))
    elif suffix == ".bpmn":
        bpmn = pm4py.read_bpmn(str(model_file))
        net, im, fm = pm4py.convert_to_petri_net(bpmn)
    else:
        raise ValueError(f"Unsupported model format: {suffix}")

    # Perform conformance checking
    if method == "token":
        result = pm4py.conformance_diagnostics_token_based_replay(log, net, im, fm)
        fitness = pm4py.fitness_token_based_replay(log, net, im, fm)
        precision = pm4py.precision_token_based_replay(log, net, im, fm)
    elif method == "alignment":
        result = pm4py.conformance_diagnostics_alignments(log, net, im, fm)
        fitness = pm4py.fitness_alignments(log, net, im, fm)
        precision = pm4py.precision_alignments(log, net, im, fm)
    else:
        raise ValueError(f"Unknown conformance method: {method}")

    # Extract fitness value
    if isinstance(fitness, dict):
        fitness_val = fitness.get("average_trace_fitness", fitness.get("log_fitness", 0))
    else:
        fitness_val = fitness

    # Calculate F1 score
    f1_score = (
        2 * fitness_val * precision / (fitness_val + precision)
        if (fitness_val + precision) > 0
        else 0
    )

    return {
        "fitness": fitness_val,
        "precision": precision,
        "f1_score": f1_score,
        "method": method,
        "num_traces": len(log),
        "results": result,
    }


def get_log_statistics(log) -> Dict[str, Any]:
    """
    Get statistics about an event log.

    Args:
        log: EventLog object

    Returns:
        Dictionary with log statistics
    """
    import pm4py
    from pm4py.statistics.traces.generic.log import case_statistics
    from pm4py.statistics.start_activities.log import get as get_start_activities
    from pm4py.statistics.end_activities.log import get as get_end_activities

    num_cases = len(log)
    num_events = sum(len(trace) for trace in log)
    avg_trace_length = num_events / num_cases if num_cases > 0 else 0

    # Activities
    activities = pm4py.get_event_attribute_values(log, "concept:name")
    num_activities = len(activities)

    # Variants
    variants = case_statistics.get_variant_statistics(log)
    num_variants = len(variants)

    # Start and end activities
    start_activities = get_start_activities.get_start_activities(log)
    end_activities = get_end_activities.get_end_activities(log)

    return {
        "num_cases": num_cases,
        "num_events": num_events,
        "num_activities": num_activities,
        "num_variants": num_variants,
        "avg_trace_length": avg_trace_length,
        "num_start_activities": len(start_activities),
        "num_end_activities": len(end_activities),
        "activities": dict(sorted(activities.items(), key=lambda x: x[1], reverse=True)),
        "start_activities": dict(
            sorted(start_activities.items(), key=lambda x: x[1], reverse=True)
        ),
        "end_activities": dict(
            sorted(end_activities.items(), key=lambda x: x[1], reverse=True)
        ),
        "variants": sorted(
            variants, key=lambda x: x.get("count", 0), reverse=True
        )[:10],  # Top 10
    }


def convert_model(
    input_file: Path,
    output_file: Path,
    input_type: str = "pnml",
    output_type: str = "bpmn",
) -> None:
    """
    Convert between process model formats.

    Args:
        input_file: Input model file
        output_file: Output model file
        input_type: Input format ('pnml' or 'bpmn')
        output_type: Output format ('pnml' or 'bpmn')

    Raises:
        ValueError: If formats are unsupported
    """
    import pm4py

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Load model
    if input_type == "pnml":
        net, im, fm = pm4py.read_pnml(str(input_file))
        model = (net, im, fm)
    elif input_type == "bpmn":
        model = pm4py.read_bpmn(str(input_file))
    else:
        raise ValueError(f"Unsupported input format: {input_type}")

    # Convert and save
    if output_type == "pnml" and input_type == "bpmn":
        net, im, fm = pm4py.convert_to_petri_net(model)
        pm4py.write_pnml(net, im, fm, str(output_file))
    elif output_type == "bpmn" and input_type == "pnml":
        net, im, fm = model
        bpmn = pm4py.convert_petri_net_to_bpmn(net, im, fm)
        pm4py.write_bpmn(bpmn, str(output_file))
    else:
        raise ValueError(
            f"Unsupported conversion: {input_type} -> {output_type}"
        )


def visualize_model(
    model: Any,
    output_file: Path,
    model_type: str = "petri",
    format: str = "png",
) -> None:
    """
    Visualize a process model.

    Args:
        model: Process model
        output_file: Output visualization file
        model_type: Type of model ('petri', 'bpmn', 'tree')
        format: Output format ('png' or 'svg')

    Raises:
        ValueError: If format is unsupported
    """
    import pm4py

    if format not in ["png", "svg"]:
        raise ValueError(f"Unsupported visualization format: {format}")

    output_with_ext = output_file.with_suffix(f".{format}")

    if model_type == "petri":
        net, im, fm = model
        pm4py.save_vis_petri_net(net, im, fm, str(output_with_ext))
    elif model_type == "bpmn":
        pm4py.save_vis_bpmn(model, str(output_with_ext))
    elif model_type == "tree":
        pm4py.save_vis_process_tree(model, str(output_with_ext))
    else:
        raise ValueError(f"Unsupported model type: {model_type}")


def filter_log(
    log,
    filter_type: str = "activity",
    filter_value: Optional[str] = None,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None,
) -> Any:
    """
    Filter an event log.

    Args:
        log: EventLog object
        filter_type: Type of filter ('activity', 'start', 'end', 'length')
        filter_value: Value to filter by
        min_length: Minimum trace length
        max_length: Maximum trace length

    Returns:
        Filtered EventLog

    Raises:
        ValueError: If filter parameters are invalid
    """
    import pm4py

    if filter_type == "activity" and filter_value:
        return pm4py.filter_event_attribute_values(
            log, "concept:name", [filter_value], True
        )
    elif filter_type == "start" and filter_value:
        return pm4py.filter_start_activities(log, [filter_value])
    elif filter_type == "end" and filter_value:
        return pm4py.filter_end_activities(log, [filter_value])
    elif filter_type == "length" and min_length is not None:
        return pm4py.filter_trace_length(log, min_length, max_length or float("inf"))
    else:
        raise ValueError(f"Invalid filter type or parameters: {filter_type}")


def sample_log(
    log,
    num_traces: Optional[int] = None,
    num_events: Optional[int] = None,
    method: str = "random",
) -> Any:
    """
    Sample from an event log.

    Args:
        log: EventLog object
        num_traces: Number of traces to sample
        num_events: Number of events to sample
        method: Sampling method ('random', 'systematic')

    Returns:
        Sampled EventLog

    Raises:
        ValueError: If parameters are invalid
    """
    import pm4py

    if method == "random":
        if num_traces:
            return pm4py.sample_log(log, n_traces=num_traces)
        elif num_events:
            return pm4py.sample_log(log, n_cases=max(1, num_events // 5))
        else:
            raise ValueError("Either num_traces or num_events must be specified")
    else:
        raise ValueError(f"Unknown sampling method: {method}")
