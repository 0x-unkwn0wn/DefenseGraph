from sqlalchemy import JSON, ForeignKey, ForeignKeyConstraint, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)

    tools = relationship("Tool", back_populates="vendor")


class CoverageRole(Base):
    __tablename__ = "coverage_roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    capability_links = relationship(
        "CapabilityCoverageRole",
        back_populates="coverage_role",
        cascade="all, delete-orphan",
    )


class Capability(Base):
    __tablename__ = "capabilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    domain: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    requires_data_sources: Mapped[bool] = mapped_column(default=False, nullable=False)
    supported_by_analytics: Mapped[bool] = mapped_column(default=False, nullable=False)
    supported_by_response: Mapped[bool] = mapped_column(default=False, nullable=False)
    requires_configuration: Mapped[bool] = mapped_column(default=False, nullable=False)
    configuration_profile_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    coverage_roles = relationship(
        "CapabilityCoverageRole",
        back_populates="capability",
        cascade="all, delete-orphan",
    )
    technique_maps = relationship("CapabilityTechniqueMap", back_populates="capability", cascade="all, delete-orphan")
    tool_capabilities = relationship("ToolCapability", back_populates="capability", cascade="all, delete-orphan")
    tool_templates = relationship("ToolCapabilityTemplate", back_populates="capability", cascade="all, delete-orphan")
    required_data_sources = relationship(
        "CapabilityRequiredDataSource",
        back_populates="capability",
        cascade="all, delete-orphan",
    )
    supported_response_actions = relationship(
        "CapabilitySupportedResponseAction",
        back_populates="capability",
        cascade="all, delete-orphan",
    )
    assessment_template = relationship(
        "CapabilityAssessmentTemplate",
        back_populates="capability",
        cascade="all, delete-orphan",
        uselist=False,
    )
    configuration_questions = relationship(
        "CapabilityConfigurationQuestion",
        back_populates="capability",
        cascade="all, delete-orphan",
        order_by="CapabilityConfigurationQuestion.id",
    )


class Technique(Base):
    __tablename__ = "techniques"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    capability_maps = relationship("CapabilityTechniqueMap", back_populates="technique", cascade="all, delete-orphan")
    relevant_scopes = relationship(
        "TechniqueRelevantScope",
        back_populates="technique",
        cascade="all, delete-orphan",
    )
    bas_validations = relationship(
        "BASValidation",
        back_populates="technique",
        cascade="all, delete-orphan",
        order_by="BASValidation.last_validation_date.desc()",
    )


class CapabilityTechniqueMap(Base):
    __tablename__ = "capability_technique_maps"

    capability_id: Mapped[int] = mapped_column(ForeignKey("capabilities.id"), primary_key=True)
    technique_id: Mapped[int] = mapped_column(ForeignKey("techniques.id"), primary_key=True)
    control_effect: Mapped[str] = mapped_column(String(20), primary_key=True)
    coverage: Mapped[str] = mapped_column(String(20), nullable=False)

    capability = relationship("Capability", back_populates="technique_maps")
    technique = relationship("Technique", back_populates="capability_maps")


class CapabilityCoverageRole(Base):
    __tablename__ = "capability_coverage_roles"
    __table_args__ = (UniqueConstraint("capability_id", "coverage_role_id", name="uq_capability_coverage_role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    capability_id: Mapped[int] = mapped_column(ForeignKey("capabilities.id"), nullable=False, index=True)
    coverage_role_id: Mapped[int] = mapped_column(ForeignKey("coverage_roles.id"), nullable=False, index=True)

    capability = relationship("Capability", back_populates="coverage_roles")
    coverage_role = relationship("CoverageRole", back_populates="capability_links")


class Tool(Base):
    __tablename__ = "tools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id"), nullable=True, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, default="Other")
    # A tool can have multiple roles simultaneously (e.g. ["control", "assurance"]).
    tool_types: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=lambda: ["control"])
    tool_type_labels: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    vendor = relationship("Vendor", back_populates="tools")
    capabilities = relationship("ToolCapability", back_populates="tool", cascade="all, delete-orphan")
    data_sources = relationship("ToolDataSource", back_populates="tool", cascade="all, delete-orphan")
    response_actions = relationship("ToolResponseAction", back_populates="tool", cascade="all, delete-orphan")


class DataSource(Base):
    __tablename__ = "data_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    tool_links = relationship("ToolDataSource", back_populates="data_source", cascade="all, delete-orphan")
    capability_requirements = relationship(
        "CapabilityRequiredDataSource",
        back_populates="data_source",
        cascade="all, delete-orphan",
    )


class ToolDataSource(Base):
    __tablename__ = "tool_data_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tool_id: Mapped[int] = mapped_column(ForeignKey("tools.id"), nullable=False, index=True)
    data_source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), nullable=False, index=True)
    ingestion_status: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")

    tool = relationship("Tool", back_populates="data_sources")
    data_source = relationship("DataSource", back_populates="tool_links")


class ResponseAction(Base):
    __tablename__ = "response_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    tool_links = relationship("ToolResponseAction", back_populates="response_action", cascade="all, delete-orphan")
    capability_links = relationship(
        "CapabilitySupportedResponseAction",
        back_populates="response_action",
        cascade="all, delete-orphan",
    )


class ToolResponseAction(Base):
    __tablename__ = "tool_response_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tool_id: Mapped[int] = mapped_column(ForeignKey("tools.id"), nullable=False, index=True)
    response_action_id: Mapped[int] = mapped_column(ForeignKey("response_actions.id"), nullable=False, index=True)
    implementation_level: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")

    tool = relationship("Tool", back_populates="response_actions")
    response_action = relationship("ResponseAction", back_populates="tool_links")


class CapabilityRequiredDataSource(Base):
    __tablename__ = "capability_required_data_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    capability_id: Mapped[int] = mapped_column(ForeignKey("capabilities.id"), nullable=False, index=True)
    data_source_id: Mapped[int] = mapped_column(ForeignKey("data_sources.id"), nullable=False, index=True)
    requirement_level: Mapped[str] = mapped_column(String(20), nullable=False, default="recommended")

    capability = relationship("Capability", back_populates="required_data_sources")
    data_source = relationship("DataSource", back_populates="capability_requirements")


class CapabilitySupportedResponseAction(Base):
    __tablename__ = "capability_supported_response_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    capability_id: Mapped[int] = mapped_column(ForeignKey("capabilities.id"), nullable=False, index=True)
    response_action_id: Mapped[int] = mapped_column(ForeignKey("response_actions.id"), nullable=False, index=True)

    capability = relationship("Capability", back_populates="supported_response_actions")
    response_action = relationship("ResponseAction", back_populates="capability_links")


class ToolCapabilityTemplate(Base):
    __tablename__ = "tool_capability_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    capability_id: Mapped[int] = mapped_column(ForeignKey("capabilities.id"), nullable=False)
    optional_tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="secondary")
    default_effect: Mapped[str] = mapped_column(String(20), nullable=False)
    default_implementation_level: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence_hint: Mapped[str | None] = mapped_column(String(20), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    capability = relationship("Capability", back_populates="tool_templates")


class ToolCapability(Base):
    __tablename__ = "tool_capabilities"
    __table_args__ = (UniqueConstraint("tool_id", "capability_id", name="uq_tool_capability"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tool_id: Mapped[int] = mapped_column(ForeignKey("tools.id"), nullable=False, index=True)
    capability_id: Mapped[int] = mapped_column(ForeignKey("capabilities.id"), nullable=False, index=True)
    control_effect_default: Mapped[str] = mapped_column(String(20), nullable=False)
    implementation_level: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence_source: Mapped[str] = mapped_column(String(20), nullable=False, default="declared")
    confidence_level: Mapped[str] = mapped_column(String(20), nullable=False, default="low")

    tool = relationship("Tool", back_populates="capabilities")
    capability = relationship("Capability", back_populates="tool_capabilities")
    assessment_answers = relationship(
        "ToolCapabilityAssessmentAnswer",
        back_populates="tool_capability",
        cascade="all, delete-orphan",
    )
    evidence_items = relationship(
        "ToolCapabilityEvidence",
        back_populates="tool_capability",
        cascade="all, delete-orphan",
    )
    configuration_profile = relationship(
        "ToolCapabilityConfigurationProfile",
        back_populates="tool_capability",
        cascade="all, delete-orphan",
        uselist=False,
    )
    configuration_answers = relationship(
        "ToolCapabilityConfigurationAnswer",
        back_populates="tool_capability",
        cascade="all, delete-orphan",
    )
    scopes = relationship(
        "ToolCapabilityScope",
        back_populates="tool_capability",
        cascade="all, delete-orphan",
    )
    technique_overrides = relationship(
        "ToolCapabilityTechniqueOverride",
        back_populates="tool_capability",
        cascade="all, delete-orphan",
    )


class ToolCapabilityTechniqueOverride(Base):
    __tablename__ = "tool_capability_technique_overrides"
    __table_args__ = (
        UniqueConstraint(
            "tool_capability_id",
            "technique_id",
            name="uq_tool_capability_technique_override",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tool_capability_id: Mapped[int] = mapped_column(
        ForeignKey("tool_capabilities.id"),
        nullable=False,
        index=True,
    )
    technique_id: Mapped[int] = mapped_column(ForeignKey("techniques.id"), nullable=False, index=True)
    control_effect_override: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    implementation_level_override: Mapped[str | None] = mapped_column(String(20), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")

    tool_capability = relationship("ToolCapability", back_populates="technique_overrides")
    technique = relationship("Technique")


class CoverageScope(Base):
    __tablename__ = "coverage_scopes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    tool_capability_scopes = relationship(
        "ToolCapabilityScope",
        back_populates="coverage_scope",
        cascade="all, delete-orphan",
    )
    technique_links = relationship(
        "TechniqueRelevantScope",
        back_populates="coverage_scope",
        cascade="all, delete-orphan",
    )


class ToolCapabilityScope(Base):
    __tablename__ = "tool_capability_scopes"
    __table_args__ = (UniqueConstraint("tool_capability_id", "coverage_scope_id", name="uq_tool_capability_scope"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tool_capability_id: Mapped[int] = mapped_column(ForeignKey("tool_capabilities.id"), nullable=False, index=True)
    coverage_scope_id: Mapped[int] = mapped_column(ForeignKey("coverage_scopes.id"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")

    tool_capability = relationship("ToolCapability", back_populates="scopes")
    coverage_scope = relationship("CoverageScope", back_populates="tool_capability_scopes")


class TechniqueRelevantScope(Base):
    __tablename__ = "technique_relevant_scopes"
    __table_args__ = (UniqueConstraint("technique_id", "coverage_scope_id", name="uq_technique_relevant_scope"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    technique_id: Mapped[int] = mapped_column(ForeignKey("techniques.id"), nullable=False, index=True)
    coverage_scope_id: Mapped[int] = mapped_column(ForeignKey("coverage_scopes.id"), nullable=False, index=True)
    relevance: Mapped[str] = mapped_column(String(20), nullable=False, default="secondary")

    technique = relationship("Technique", back_populates="relevant_scopes")
    coverage_scope = relationship("CoverageScope", back_populates="technique_links")


class CapabilityAssessmentTemplate(Base):
    __tablename__ = "capability_assessment_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    capability_id: Mapped[int] = mapped_column(ForeignKey("capabilities.id"), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")

    capability = relationship("Capability", back_populates="assessment_template")
    questions = relationship(
        "CapabilityAssessmentQuestion",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="CapabilityAssessmentQuestion.position",
    )


class CapabilityAssessmentQuestion(Base):
    __tablename__ = "capability_assessment_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("capability_assessment_templates.id"), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    template = relationship("CapabilityAssessmentTemplate", back_populates="questions")
    answers = relationship("ToolCapabilityAssessmentAnswer", back_populates="question", cascade="all, delete-orphan")


class ToolCapabilityAssessmentAnswer(Base):
    __tablename__ = "tool_capability_assessment_answers"

    tool_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    capability_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("capability_assessment_questions.id"), primary_key=True)
    answer: Mapped[str] = mapped_column(String(20), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tool_id", "capability_id"],
            ["tool_capabilities.tool_id", "tool_capabilities.capability_id"],
            ondelete="CASCADE",
        ),
    )

    tool_capability = relationship(
        "ToolCapability",
        back_populates="assessment_answers",
        primaryjoin=(
            "and_("
            "ToolCapabilityAssessmentAnswer.tool_id == ToolCapability.tool_id, "
            "ToolCapabilityAssessmentAnswer.capability_id == ToolCapability.capability_id"
            ")"
        ),
    )
    question = relationship("CapabilityAssessmentQuestion", back_populates="answers")


class ToolCapabilityEvidence(Base):
    __tablename__ = "tool_capability_evidence"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tool_id: Mapped[int] = mapped_column(Integer, nullable=False)
    capability_id: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence_type: Mapped[str] = mapped_column(String(100), nullable=False)
    note: Mapped[str] = mapped_column(Text, nullable=False, default="")
    file_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recorded_at: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tool_id", "capability_id"],
            ["tool_capabilities.tool_id", "tool_capabilities.capability_id"],
            ondelete="CASCADE",
        ),
    )

    tool_capability = relationship(
        "ToolCapability",
        back_populates="evidence_items",
        primaryjoin=(
            "and_("
            "ToolCapabilityEvidence.tool_id == ToolCapability.tool_id, "
            "ToolCapabilityEvidence.capability_id == ToolCapability.capability_id"
            ")"
        ),
    )


class CapabilityConfigurationQuestion(Base):
    __tablename__ = "capability_configuration_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    capability_id: Mapped[int] = mapped_column(ForeignKey("capabilities.id"), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    applies_to_profile_type: Mapped[str | None] = mapped_column(String(50), nullable=True)

    capability = relationship("Capability", back_populates="configuration_questions")
    answers = relationship(
        "ToolCapabilityConfigurationAnswer",
        back_populates="question_ref",
        cascade="all, delete-orphan",
    )


class ToolCapabilityConfigurationProfile(Base):
    __tablename__ = "tool_capability_configuration_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tool_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    capability_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    profile_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    configuration_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unknown")
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    last_updated_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tool_id", "capability_id"],
            ["tool_capabilities.tool_id", "tool_capabilities.capability_id"],
            ondelete="CASCADE",
        ),
    )

    tool_capability = relationship(
        "ToolCapability",
        back_populates="configuration_profile",
        primaryjoin=(
            "and_("
            "ToolCapabilityConfigurationProfile.tool_id == ToolCapability.tool_id, "
            "ToolCapabilityConfigurationProfile.capability_id == ToolCapability.capability_id"
            ")"
        ),
    )


class ToolCapabilityConfigurationAnswer(Base):
    __tablename__ = "tool_capability_configuration_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tool_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    capability_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    question_id: Mapped[int] = mapped_column(ForeignKey("capability_configuration_questions.id"), nullable=False)
    answer: Mapped[str] = mapped_column(String(20), nullable=False)

    __table_args__ = (
        ForeignKeyConstraint(
            ["tool_id", "capability_id"],
            ["tool_capabilities.tool_id", "tool_capabilities.capability_id"],
            ondelete="CASCADE",
        ),
    )

    tool_capability = relationship(
        "ToolCapability",
        back_populates="configuration_answers",
        primaryjoin=(
            "and_("
            "ToolCapabilityConfigurationAnswer.tool_id == ToolCapability.tool_id, "
            "ToolCapabilityConfigurationAnswer.capability_id == ToolCapability.capability_id"
            ")"
        ),
    )
    question_ref = relationship("CapabilityConfigurationQuestion", back_populates="answers")


class BASValidation(Base):
    """Per-technique BAS (Breach and Attack Simulation) test result.

    BAS is a cross-functional assurance capability, not an active security
    control.  These records track whether a specific TTP has been validated
    by a BAS tool and what the outcome was.
    """

    __tablename__ = "bas_validations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    technique_id: Mapped[int] = mapped_column(ForeignKey("techniques.id"), nullable=False, index=True)
    # Optional reference to the BAS tool that ran the test (tool_type == "assurance")
    bas_tool_id: Mapped[int | None] = mapped_column(ForeignKey("tools.id"), nullable=True, index=True)
    # "blocked" | "detected" | "not_detected" | "not_tested"
    bas_result: Mapped[str] = mapped_column(String(20), nullable=False, default="not_tested")
    last_validation_date: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")

    technique = relationship("Technique", back_populates="bas_validations")
    bas_tool = relationship("Tool", foreign_keys=[bas_tool_id])
