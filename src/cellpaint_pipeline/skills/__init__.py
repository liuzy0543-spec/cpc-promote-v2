"""The documented skill catalog and the single entry point that runs a skill.

LAYOUT
------
``definitions``  immutable value objects exchanged across the skill layer
``catalog``      the skill catalog itself (primary / advanced / legacy entries)
``inputs``       the parameter object plus the two accepted call shapes
``context``      the runtime context handed to a runner
``registry``     the skill-key -> runner table
``dispatch``     :func:`run_pipeline_skill`, the public entry point
``finalize``     shared manifest/result assembly
``runners``      the runners, grouped by pipeline stage

Everything that used to be importable from ``cellpaint_pipeline.skills`` is
still importable from here, so this module doubles as the compatibility
facade for the pre-split single-file layout.
"""
from __future__ import annotations

from cellpaint_pipeline.skills.catalog import (
    ADVANCED_PIPELINE_SKILLS,
    ALL_PIPELINE_SKILLS,
    CURRENT_ADVANCED_PIPELINE_SKILLS,
    CURRENT_LEGACY_PIPELINE_SKILLS,
    CURRENT_PRIMARY_PIPELINE_SKILLS,
    LEGACY_PIPELINE_SKILLS,
    PRIMARY_PIPELINE_SKILLS,
    available_pipeline_skills,
    get_pipeline_skill_definition,
)
from cellpaint_pipeline.skills.context import SkillRuntimeContext
from cellpaint_pipeline.skills.definitions import (
    PipelineSkillDefinition,
    PipelineSkillResult,
    pipeline_skill_definition_to_dict,
    pipeline_skill_result_to_dict,
)
from cellpaint_pipeline.skills.dispatch import run_pipeline_skill
from cellpaint_pipeline.skills.finalize import (
    _build_isolated_segmentation_skill_config,
    _execution_result_to_dict,
    _finalize_skill_result,
    _json_ready,
    _resolve_segmentation_source_config,
)
from cellpaint_pipeline.skills.inputs import (
    DEPRECATED_SKILL_PARAMETERS,
    SkillInputs,
    assemble_skill_inputs,
    skill_inputs_from_mapping,
    skill_inputs_to_mapping,
)
from cellpaint_pipeline.skills.registry import SKILL_RUNNERS

# The native implementations the runners call are re-exported here for two
# reasons: they were importable from ``cellpaint_pipeline.skills`` before the
# split, and tests patch them at that location to isolate a runner.  Keeping the
# names available preserves both the public surface and that patching seam.
from cellpaint_pipeline.profile_summaries import (  # noqa: E402  (compat re-export)
    summarize_classical_profiles,
    summarize_deepprofiler_profiles,
)
from cellpaint_pipeline.profiling_native import (  # noqa: E402  (compat re-export)
    export_cellprofiler_to_singlecell_native,
    run_pycytominer_aggregate_native,
    run_pycytominer_annotate_native,
    run_pycytominer_feature_select_native,
    run_pycytominer_native,
    run_pycytominer_normalize_native,
)
from cellpaint_pipeline.segmentation_native import (  # noqa: E402  (compat re-export)
    build_mask_export_pipeline_native,
    extract_single_cell_crops_native,
    generate_sample_previews_native,
    prepare_segmentation_load_data_native,
)
from cellpaint_pipeline.workflows.profiling import run_profiling_script  # noqa: E402
from cellpaint_pipeline.workflows.segmentation import run_segmentation_script  # noqa: E402
from cellpaint_pipeline.skills.runners.data_access import (
    _resolve_download_request_and_plan,
    _run_data_plan_download,
    _run_download_cellpainting_data,
    _run_inspect_cellpainting_data,
)
from cellpaint_pipeline.skills.runners.deepprofiler import (
    _run_build_deepprofiler_project,
    _run_collect_deepprofiler_features,
    _run_deepprofiler,
    _run_deepprofiler_profile,
    _run_export_deepprofiler_inputs,
    _run_prepare_deepprofiler_project,
    _run_summarize_deepprofiler_profiles,
)
from cellpaint_pipeline.skills.runners.profiling import (
    _run_cellprofiler_profiling,
    _run_cyto_aggregate_profiles,
    _run_cyto_annotate_profiles,
    _run_cyto_normalize_profiles,
    _run_cyto_select_profile_features,
    _run_export_single_cell_measurements,
    _run_pycytominer,
    _run_pycytominer_stage,
    _run_summarize_classical_profiles,
)
from cellpaint_pipeline.skills.runners.segmentation import (
    _run_export_masked_single_cell_crops,
    _run_export_single_cell_crops,
    _run_export_unmasked_single_cell_crops,
    _run_extract_segmentation_artifacts,
    _run_generate_sample_previews,
    _run_prepare_segmentation_inputs,
    _run_segmentation_masks,
    _run_single_cell_crop_skill,
)

__all__ = [
    'ADVANCED_PIPELINE_SKILLS',
    'ALL_PIPELINE_SKILLS',
    'CURRENT_ADVANCED_PIPELINE_SKILLS',
    'CURRENT_LEGACY_PIPELINE_SKILLS',
    'CURRENT_PRIMARY_PIPELINE_SKILLS',
    'DEPRECATED_SKILL_PARAMETERS',
    'LEGACY_PIPELINE_SKILLS',
    'PRIMARY_PIPELINE_SKILLS',
    'PipelineSkillDefinition',
    'PipelineSkillResult',
    'SKILL_RUNNERS',
    'SkillInputs',
    'SkillRuntimeContext',
    'assemble_skill_inputs',
    'available_pipeline_skills',
    'get_pipeline_skill_definition',
    'pipeline_skill_definition_to_dict',
    'pipeline_skill_result_to_dict',
    'run_pipeline_skill',
    'skill_inputs_from_mapping',
    'skill_inputs_to_mapping',
]
