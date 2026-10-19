"""oscal_factory.py — typed factory API for oscal-compass/compliance-trestle objects.

All trestle OSCAL class construction for this project flows through this module.
Callers work exclusively with the factory functions below; direct imports of
trestle internals are contained here and nowhere else.

Observation idref props follow the pattern established by the oscal-compass
e2e-demo-compliance-posture reference implementation:
  - ``assessment-rule-id``  (no ns) — matches Rule_Id in the validation component
  - ``idref``               (CNCF_OSCAL_NS) — matches Check_Id in the validation component
  - ``result``              (CNCF_OSCAL_NS) — pass / fail / other
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from trestle.oscal import OSCAL_VERSION
from trestle.oscal import assessment_plan as ap_mod
from trestle.oscal import assessment_results as ar_mod
from trestle.oscal import common
from trestle.oscal import component as comp_mod
from trestle.oscal import ssp as ssp_mod

# Namespace used across all CNCF OSCAL properties in this project.
CNCF_OSCAL_NS = "https://oscal-compass/compliance-trestle/schemas/oscal/cd"


# ---------------------------------------------------------------------------
# Low-level primitives
# ---------------------------------------------------------------------------

def new_uuid() -> str:
    """Return a fresh RFC-4122 v4 UUID string."""
    return str(uuid.uuid4())


def now_utc() -> datetime:
    """Return the current UTC datetime."""
    return datetime.now(tz=timezone.utc)


def prop(name: str, value: str, ns: str | None = None,
         remarks: str | None = None) -> common.Property:
    """Construct a trestle ``Property`` with an optional OSCAL namespace."""
    return common.Property(name=name, value=value, ns=ns, remarks=remarks)


def cncf_prop(name: str, value: str,
              remarks: str | None = None) -> common.Property:
    """Construct a ``Property`` in the CNCF OSCAL namespace."""
    return prop(name, value, ns=CNCF_OSCAL_NS, remarks=remarks)


def set_parameter(param_id: str, value: str,
                  remarks: str | None = None) -> common.SetParameter:
    """Construct a trestle ``SetParameter``."""
    return common.SetParameter(**{"param-id": param_id}, values=[value],
                               remarks=remarks)


def metadata(title: str, version: str = "1.0") -> common.Metadata:
    """Construct a ``Metadata`` block with current timestamp and OSCAL version."""
    return common.Metadata(
        title=title,
        **{"last-modified": now_utc()},
        version=version,
        **{"oscal-version": OSCAL_VERSION},
    )


def org_metadata(title: str, org_name: str,
                 org_href: str | None = None) -> common.Metadata:
    """``Metadata`` block with a single organisation party."""
    party_kwargs: dict = {
        "uuid": new_uuid(), "type": "organization", "name": org_name,
    }
    if org_href:
        party_kwargs["links"] = [common.Link(href=org_href, rel="canonical")]
    md = metadata(title)
    md.parties = [common.Parties(**party_kwargs)]
    return md


# ---------------------------------------------------------------------------
# Observation / Finding builders (assessment results)
# ---------------------------------------------------------------------------

def observation(
    *,
    title: str,
    description: str,
    rule_id: str,
    check_id: str,
    result: str,
    method: str = "TEST",
    collected: datetime | None = None,
) -> tuple[str, common.Observation]:
    """Build an ``Observation`` with comp-def idref props.

    Returns ``(obs_uuid, Observation)`` so the caller can wire up the
    corresponding ``Finding.related-observations`` without a second lookup.

    Props added (matching the oscal-compass e2e-demo pattern, present on
    every observation in that reference implementation):

    * ``assessment-rule-id`` (no ns) — maps to ``Rule_Id`` in the validation
      component of the component definition.
    * ``idref`` (CNCF ns) — maps to ``Check_Id`` in the validation component.
    * ``result`` (CNCF ns) — scanner outcome: pass / fail / no-result / no-check.
    """
    obs_uuid = new_uuid()
    obs = common.Observation(
        uuid=obs_uuid,
        title=title,
        description=description,
        props=[
            prop("assessment-rule-id", rule_id),
            cncf_prop("idref", check_id),
            cncf_prop("result", result),
        ],
        methods=[method],
        collected=collected or now_utc(),
    )
    return obs_uuid, obs


def finding(
    *,
    title: str,
    description: str,
    control_id: str,
    state: str,
    reason: str,
    obs_uuid: str,
) -> common.Finding:
    """Build a ``Finding`` linked to a previously created observation UUID."""
    state_val = (
        common.ObjectiveStatusStateValidValues.satisfied
        if state == "satisfied"
        else common.ObjectiveStatusStateValidValues.not_satisfied
    )
    reason_map = {
        "pass": common.Reason.pass_,
        "fail": common.Reason.fail,
        "no-result": common.Reason.other,
        "no-check": common.Reason.other,
    }
    return common.Finding(
        uuid=new_uuid(),
        title=title,
        description=description,
        target=common.FindingTarget(
            type=common.FindingTargetTypeValidValues.objective_id,
            **{"target-id": control_id},
            status=common.ObjectiveStatus(
                state=state_val,
                reason=reason_map[reason],
            ),
        ),
        **{"related-observations": [
            common.RelatedObservation(**{"observation-uuid": obs_uuid})
        ]},
    )


def assessment_results(
    *,
    repo_name: str,
    slug: str,
    observations: list[common.Observation],
    findings: list[common.Finding],
    outcomes: list[dict],
    start: datetime,
    end: datetime,
) -> ar_mod.Model:
    """Assemble a complete ``AssessmentResults`` OSCAL model."""
    result = ar_mod.Result(
        uuid=new_uuid(),
        title=f"Automated assessment - {repo_name}",
        description=(
            "Automated evidence checks defined by the cncf-repo component definition."
        ),
        start=start,
        end=end,
        **{"reviewed-controls": common.ReviewedControls(
            **{"control-selections": [common.ControlSelections(
                **{"include-controls": [
                    common.SelectControlById(**{"control-id": o["control_id"]})
                    for o in outcomes
                ]}
            )]}
        )},
        observations=observations,
        findings=findings,
    )
    return ar_mod.Model(**{"assessment-results": ar_mod.AssessmentResults(
        uuid=new_uuid(),
        metadata=metadata(f"Assessment Results - {repo_name}"),
        **{"import-ap": ar_mod.ImportAp(
            href=f"trestle://assessment-plans/{slug}/assessment-plan.json"
        )},
        results=[result],
    )})


# ---------------------------------------------------------------------------
# Component definition builders
# ---------------------------------------------------------------------------

def software_component(
    *,
    title: str,
    description: str,
    purpose: str,
    sw_props: list[common.Property],
    control_implementations: list[comp_mod.ControlImplementation],
) -> comp_mod.DefinedComponent:
    """Build a ``software`` DefinedComponent."""
    return comp_mod.DefinedComponent(
        uuid=new_uuid(), type="software", title=title,
        description=description, purpose=purpose,
        props=sw_props,
        **{"control-implementations": control_implementations},
    )


def validation_component(
    *,
    title: str,
    description: str,
    purpose: str,
    val_props: list[common.Property],
) -> comp_mod.DefinedComponent:
    """Build a ``validation`` DefinedComponent (no control-implementations)."""
    return comp_mod.DefinedComponent(
        uuid=new_uuid(), type="validation", title=title,
        description=description, purpose=purpose, props=val_props,
    )


def project_software_component(
    *,
    repo_name: str,
    repo_url: str,
    control_implementations: list[comp_mod.ControlImplementation],
) -> comp_mod.DefinedComponent:
    """Build the per-project ``software`` DefinedComponent."""
    return comp_mod.DefinedComponent(
        uuid=new_uuid(), type="software",
        title=repo_name,
        description=f"Source code repository at {repo_url}.",
        purpose="CNCF project source repository assessed against the cncf-repo profile.",
        links=[common.Link(href=repo_url, rel="reference")],
        **{"control-implementations": control_implementations},
    )


def component_definition(
    *,
    md: common.Metadata,
    components: list[comp_mod.DefinedComponent],
    imports: list[comp_mod.ImportComponentDefinition] | None = None,
) -> comp_mod.Model:
    """Wrap components (and optional imports) into a ``ComponentDefinition`` model."""
    kwargs: dict = {
        "uuid": new_uuid(), "metadata": md, "components": components,
    }
    if imports:
        kwargs["import-component-definitions"] = imports
    return comp_mod.Model(
        **{"component-definition": comp_mod.ComponentDefinition(**kwargs)}
    )


# ---------------------------------------------------------------------------
# SSP helpers
# ---------------------------------------------------------------------------

def system_component_from_defined(
    defined: comp_mod.DefinedComponent,
    comp_def_href: str,
) -> common.SystemComponent:
    """Convert a ``DefinedComponent`` into a ``SystemComponent`` for use in the SSP.

    Preserves the original UUID so that ``by-components[].component-uuid``
    references in ``implemented-requirements`` resolve correctly.  Adds an
    ``imported-from`` link back to the source component definition, following
    the OSCAL convention used by ``trestle author ssp``.

    The ``control-implementations`` field is dropped — it belongs in the
    comp-def, not the SSP system-implementation.
    """
    existing_links = list(defined.links or [])
    imported_link = common.Link(href=comp_def_href, rel="imported-from")
    return common.SystemComponent(
        uuid=defined.uuid,
        type=str(defined.type),
        title=defined.title,
        description=defined.description,
        purpose=defined.purpose,
        props=defined.props or None,
        links=existing_links + [imported_link],
        status=common.Status(
            state=common.SystemComponentOperationalStateValidValues.operational
        ),
    )


# ---------------------------------------------------------------------------
# SSP builder
# ---------------------------------------------------------------------------

def system_security_plan(
    *,
    repo_name: str,
    repo_url: str,
    profile_href: str,
    system_components: list[common.SystemComponent],
    implemented: list[ssp_mod.ImplementedRequirement],
) -> ssp_mod.Model:
    """Assemble a complete ``SystemSecurityPlan`` OSCAL model.

    ``system_components`` should be built from every ``DefinedComponent`` in
    all referenced component definitions via ``system_component_from_defined()``.
    Their UUIDs are preserved so that ``by-components[].component-uuid`` entries
    in ``implemented-requirements`` form a closed reference loop.
    """
    ssp = ssp_mod.SystemSecurityPlan(
        uuid=new_uuid(),
        metadata=org_metadata(
            f"System Security Plan — {repo_name}",
            org_name=repo_name,
            org_href=repo_url,
        ),
        **{"import-profile": ssp_mod.ImportProfile(href=profile_href)},
        **{"system-characteristics": ssp_mod.SystemCharacteristics(
            **{
                "system-ids": [common.SystemId(
                    **{"identifier-type": "https://github.com"}, id=repo_url
                )],
                "system-name": repo_name,
                "description": (
                    f"Source code repository at {repo_url}, "
                    "assessed against the CNCF cncf-repo profile."
                ),
                "status": ssp_mod.Status1(
                    state=ssp_mod.OperationalStateValidValues.operational
                ),
                "authorization-boundary": ssp_mod.AuthorizationBoundary(
                    description=(
                        "The source code repository, its build pipeline, "
                        "dependency declarations, branch protection settings, "
                        "and committed artifacts."
                    )
                ),
                "system-information": ssp_mod.SystemInformation(
                    **{"information-types": [
                        ssp_mod.InformationType(
                            uuid=new_uuid(),
                            title="Source Code and Build Artifacts",
                            description=(
                                "Source code, scripts, configuration files, "
                                "dependency declarations, and generated OSCAL artifacts."
                            ),
                        )
                    ]}
                ),
            }
        )},
        **{"system-implementation": ssp_mod.SystemImplementation(
            components=system_components,
            users=[
                common.SystemUser(
                    uuid=new_uuid(),
                    title="Repository Contributor",
                    **{"short-name": "contributor"},
                    description="Developer with commit access to the repository.",
                    **{"role-ids": ["developer"]},
                )
            ],
        )},
        **{"control-implementation": ssp_mod.ControlImplementation(
            description=(
                "Implementation of cncf-repo profile controls. "
                "Parameter values are specific to this repository."
            ),
            **{"implemented-requirements": implemented},
        )},
    )
    return ssp_mod.Model(**{"system-security-plan": ssp})


# ---------------------------------------------------------------------------
# Assessment Plan builder
# ---------------------------------------------------------------------------

def assessment_plan(
    *,
    repo_name: str,
    slug: str,
    control_ids: list[str],
) -> ap_mod.Model:
    """Build a complete ``AssessmentPlan`` model selecting all given control IDs."""
    ap = ap_mod.AssessmentPlan(
        uuid=new_uuid(),
        metadata=metadata(f"Assessment Plan — {repo_name}"),
        **{"import-ssp": common.ImportSsp(
            href=f"trestle://system-security-plans/{slug}/system-security-plan.json"
        )},
        **{"reviewed-controls": common.ReviewedControls(
            description="All controls selected by the cncf-repo profile.",
            **{"control-selections": [common.ControlSelections(
                **{"include-controls": [
                    common.SelectControlById(**{"control-id": cid})
                    for cid in control_ids
                ]}
            )]},
        )},
        **{"assessment-subjects": [common.AssessmentSubjectAll(
            type="component",
            description="The source code repository component.",
            **{"include-all": common.IncludeAll()},
        )]},
    )
    return ap_mod.Model(**{"assessment-plan": ap})
