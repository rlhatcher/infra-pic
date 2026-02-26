"""Custom exception hierarchy for awsdiagram."""


class AwsDiagramError(Exception):
    """Base exception for all awsdiagram errors."""


class YamlLoadError(AwsDiagramError):
    """Failed to load or parse YAML file."""


class SchemaValidationError(AwsDiagramError):
    """YAML content doesn't match the expected schema."""


class ServiceReferenceError(AwsDiagramError):
    """A group or connection references a service ID that doesn't exist."""


class TypeResolutionError(AwsDiagramError):
    """Failed to resolve a service type to a diagrams class."""


class GraphvizNotFoundError(AwsDiagramError):
    """Graphviz 'dot' binary not found on PATH."""


class RenderError(AwsDiagramError):
    """Failed to render the diagram."""


class TerraformImportError(AwsDiagramError):
    """Failed to import a Terraform plan or state file."""
