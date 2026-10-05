from __future__ import annotations

"""Public entry point that turns skill inputs into a skill run."""

from pathlib import Path
from typing import TYPE_CHECKING

from cellpaint_pipeline.config import ProjectConfig
from cellpaint_pipeline.skills.catalog import get_pipeline_skill_definition
from cellpaint_pipeline.skills.context import SkillRuntimeContext
from cellpaint_pipeline.skills.definitions import PipelineSkillResult
from cellpaint_pipeline.skills.inputs import (
    DEPRECATED_SKILL_PARAMETERS,
    SkillInputs,
    assemble_skill_inputs,
)
from cellpaint_pipeline.skills.registry import SKILL_RUNNERS

# Annotations only: importing data_access here would pull the whole data-access
# package into every "import ...skills.dispatch".  The guard keeps type checkers
# accurate at no runtime cost, which is why typing.get_type_hints() is not
# supported on these entry points (nor on context/inputs, which do the same).
if TYPE_CHECKING:
    from cellpaint_pipeline.data_access import DataDownloadPlan, DataRequest


def run_pipeline_skill(
    config: ProjectConfig,
    skill_key: str,
    *,
    inputs: SkillInputs | None = None,
    output_dir: Path | None = None,
    data_request: DataRequest | None = None,
    download_plan: DataDownloadPlan | None = None,
    workflow_root: Path | None = None,
    export_root: Path | None = None,
    project_root: Path | None = None,
    image_csv_path: Path | None = None,
    nuclei_csv_path: Path | None = None,
    load_data_csv_path: Path | None = None,
    manifest_path: Path | None = None,
    object_table_path: Path | None = None,
    single_cell_path: Path | None = None,
    aggregated_path: Path | None = None,
    annotated_path: Path | None = None,
    normalized_path: Path | None = None,
    feature_selected_path: Path | None = None,
    single_cell_parquet_path: Path | None = None,
    well_aggregated_parquet_path: Path | None = None,
    object_table: str | None = None,
    crop_mode: str | None = None,
    gpu: str | None = None,
    experiment_name: str | None = None,
    config_filename: str | None = None,
    metadata_filename: str | None = None,
    workers: int = 0,
    chunk_size: int = 64,
    overwrite: bool = False,
    profiling_suite: str | None = None,
    segmentation_suite: str | None = None,
    deepprofiler_mode: str | None = None,
    include_validation_report: bool | None = None,
    include_data_access_summary: bool | None = None,
    plan_data_download: bool | None = None,
    execute_data_download_step: bool | None = None,
) -> PipelineSkillResult:
    """Run one catalog skill.

    Two call shapes are supported and are fully interchangeable:

    * the historical flat keyword form (``output_dir=...`` and friends),
    * the object form (``inputs=SkillInputs(output_dir=...)``).

    The parameters listed in :data:`DEPRECATED_SKILL_PARAMETERS` are
    accepted for backwards compatibility only; they never influenced the
    result and now emit a :class:`DeprecationWarning`.
    """
    resolved = assemble_skill_inputs(
        config,
        inputs,
        output_dir=output_dir,
        data_request=data_request,
        download_plan=download_plan,
        workflow_root=workflow_root,
        export_root=export_root,
        project_root=project_root,
        image_csv_path=image_csv_path,
        nuclei_csv_path=nuclei_csv_path,
        load_data_csv_path=load_data_csv_path,
        manifest_path=manifest_path,
        object_table_path=object_table_path,
        single_cell_path=single_cell_path,
        aggregated_path=aggregated_path,
        annotated_path=annotated_path,
        normalized_path=normalized_path,
        feature_selected_path=feature_selected_path,
        single_cell_parquet_path=single_cell_parquet_path,
        well_aggregated_parquet_path=well_aggregated_parquet_path,
        object_table=object_table,
        crop_mode=crop_mode,
        gpu=gpu,
        experiment_name=experiment_name,
        config_filename=config_filename,
        metadata_filename=metadata_filename,
        workers=workers,
        chunk_size=chunk_size,
        overwrite=overwrite,
        profiling_suite=profiling_suite,
        segmentation_suite=segmentation_suite,
        deepprofiler_mode=deepprofiler_mode,
        include_validation_report=include_validation_report,
        include_data_access_summary=include_data_access_summary,
        plan_data_download=plan_data_download,
        execute_data_download_step=execute_data_download_step,
    )

    definition = get_pipeline_skill_definition(skill_key)
    if definition.status == 'legacy':
        replacements = ', '.join(definition.replaced_by) or 'the primary skill catalog'
        raise KeyError(f'Legacy pipeline skill {skill_key!r} is no longer executable. Use: {replacements}')

    run_root = resolved.output_dir.resolve() if resolved.output_dir is not None else (config.default_output_root / 'skills' / skill_key)
    run_root.mkdir(parents=True, exist_ok=True)
    context = SkillRuntimeContext(
        config=config,
        definition=definition,
        run_root=run_root,
        data_request=resolved.data_request,
        download_plan=resolved.download_plan,
        workflow_root=resolved.workflow_root,
        export_root=resolved.export_root,
        project_root=resolved.project_root,
        image_csv_path=resolved.image_csv_path,
        nuclei_csv_path=resolved.nuclei_csv_path,
        load_data_csv_path=resolved.load_data_csv_path,
        manifest_path=resolved.manifest_path,
        object_table_path=resolved.object_table_path,
        single_cell_path=resolved.single_cell_path,
        aggregated_path=resolved.aggregated_path,
        annotated_path=resolved.annotated_path,
        normalized_path=resolved.normalized_path,
        feature_selected_path=resolved.feature_selected_path,
        single_cell_parquet_path=resolved.single_cell_parquet_path,
        well_aggregated_parquet_path=resolved.well_aggregated_parquet_path,
        object_table=resolved.object_table,
        crop_mode=resolved.crop_mode,
        gpu=resolved.gpu,
        experiment_name=resolved.experiment_name,
        config_filename=resolved.config_filename,
        metadata_filename=resolved.metadata_filename,
        workers=resolved.workers,
        chunk_size=resolved.chunk_size,
        overwrite=resolved.overwrite,
    )
    return SKILL_RUNNERS[skill_key](context)
