"""GitHub versions of the TrainingMaterial plugins."""
from app.layer_3.plugins.github.github_base_extractor import GitHubBaseExtractor
from app.layer_3.plugins.shared.training.collection import (
    TrainingAbstractExtractor,
    TrainingAuthorExtractor,
    TrainingConditionsOfAccessExtractor,
    TrainingDescriptionExtractor,
    TrainingInLanguageExtractor,
    TrainingLearningResourceTypeExtractor,
    TrainingNameExtractor,
    TrainingSourceRepositoryExtractor,
)


class GitHubTrainingNameExtractor(TrainingNameExtractor, GitHubBaseExtractor):
    name = "github.training.name"


class GitHubTrainingDescriptionExtractor(TrainingDescriptionExtractor, GitHubBaseExtractor):
    name = "github.training.description"


class GitHubTrainingAbstractExtractor(TrainingAbstractExtractor, GitHubBaseExtractor):
    name = "github.training.abstract"


class GitHubTrainingAuthorExtractor(TrainingAuthorExtractor, GitHubBaseExtractor):
    name = "github.training.author"


class GitHubTrainingInLanguageExtractor(TrainingInLanguageExtractor, GitHubBaseExtractor):
    name = "github.training.in_language"


class GitHubTrainingLearningResourceTypeExtractor(TrainingLearningResourceTypeExtractor, GitHubBaseExtractor):
    name = "github.training.learning_resource_type"


class GitHubTrainingSourceRepositoryExtractor(TrainingSourceRepositoryExtractor, GitHubBaseExtractor):
    name = "github.training.source_repository"


class GitHubTrainingConditionsOfAccessExtractor(TrainingConditionsOfAccessExtractor, GitHubBaseExtractor):
    name = "github.training.conditions_of_access"
