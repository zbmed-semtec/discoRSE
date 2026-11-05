"""Platform-independent plugins for the TrainingMaterial schema."""
from app.layer_3.plugins.shared.git_platform_base_extractor import GitPlatformBaseExtractor
from app.layer_3.plugins.shared.training import parsers

SDO = "https://schema.org/"
DRAFTS = "https://discovery.biothings.io/ns/bioschemasdrafts/"


class TrainingPlugin(GitPlatformBaseExtractor):
    """Limits a plugin to the TrainingMaterial schema, so software schemas are unaffected."""

    def applicable(self, context):
        return super().applicable(context) and context.schema.get_schema_name() == "TrainingMaterial"


class TrainingNameExtractor(TrainingPlugin):
    """Prefer the course title over the repository slug (Platform API, confidence 0.95)."""

    extracts = {f"{SDO}name"}

    def extract(self, context, state):
        client = self.get_client(context, state)
        for config in parsers.get_site_configs(client):
            if "title" in config:
                state.metadata_collector.collect("Site Config", f"{SDO}name", config["title"], 0.98)
        for cff in client.get_parsed_citations():
            if isinstance(cff.get("title"), str) and cff["title"].strip():
                state.metadata_collector.collect("CFF File", f"{SDO}name", cff["title"].strip(), 0.97)
        readme = parsers.get_root_readme(client)
        title = parsers.readme_title(readme) if readme else None
        if title:
            state.metadata_collector.collect("README", f"{SDO}name", title, 0.96)
        return state


class TrainingDescriptionExtractor(TrainingPlugin):
    """Fallbacks for when the repository has no description."""

    extracts = {f"{SDO}description"}

    def extract(self, context, state):
        client = self.get_client(context, state)
        for config in parsers.get_site_configs(client):
            if "description" in config:
                state.metadata_collector.collect("Site Config", f"{SDO}description", config["description"], 0.85)
        readme = parsers.get_root_readme(client)
        paragraph = parsers.readme_first_paragraph(readme) if readme else None
        if paragraph:
            state.metadata_collector.collect("README", f"{SDO}description", paragraph, 0.5)
        return state


class TrainingAbstractExtractor(TrainingPlugin):
    extracts = {f"{SDO}abstract"}

    def extract(self, context, state):
        client = self.get_client(context, state)
        for cff in client.get_parsed_citations():
            if isinstance(cff.get("abstract"), str):
                state.metadata_collector.collect("CFF File", f"{SDO}abstract", cff["abstract"], 0.9)
        return state


class TrainingAuthorExtractor(TrainingPlugin):
    """Fallback for repositories without CITATION.cff; CFF authors keep priority (0.90)."""

    extracts = {f"{SDO}author"}

    def extract(self, context, state):
        client = self.get_client(context, state)
        for config in parsers.get_site_configs(client):
            authors = [{"@type": "Person", "name": name} for name in config.get("authors", [])]
            if authors:
                state.metadata_collector.collect("Site Config", f"{SDO}author", authors, 0.8)
        return state


class TrainingInLanguageExtractor(TrainingPlugin):
    extracts = {f"{SDO}inLanguage"}

    def extract(self, context, state):
        client = self.get_client(context, state)
        for config in parsers.get_site_configs(client):
            if "language" in config:
                state.metadata_collector.collect("Site Config", f"{SDO}inLanguage", [config["language"]], 0.85)
        for cff in client.get_parsed_citations():
            if isinstance(cff.get("languages"), list) and cff["languages"]:
                state.metadata_collector.collect("CFF File", f"{SDO}inLanguage", cff["languages"], 0.9)
        return state


class TrainingLearningResourceTypeExtractor(TrainingPlugin):
    extracts = {f"{SDO}learningResourceType"}

    def extract(self, context, state):
        client = self.get_client(context, state)
        paths = [entry.path for entry in client.list_contents()]
        types = parsers.detect_learning_resource_types(paths)
        if types:
            state.metadata_collector.collect("File Pattern", f"{SDO}learningResourceType", types, 0.6)
        return state


class TrainingSourceRepositoryExtractor(TrainingPlugin):
    extracts = {f"{DRAFTS}sourceRepository"}

    def extract(self, context, state):
        url = self.get_client(context, state).get_html_url()
        if url:
            state.metadata_collector.collect("Platform API", f"{DRAFTS}sourceRepository", url, 0.95)
        return state


class TrainingConditionsOfAccessExtractor(TrainingPlugin):
    """Fills schema:conditionsOfAccess, which the existing GitHub plugins misspell."""

    extracts = {f"{SDO}conditionsOfAccess"}

    def extract(self, context, state):
        private = self.get_client(context, state).get_repository().get("private")
        if private is False:
            state.metadata_collector.collect("Platform API", f"{SDO}conditionsOfAccess", "Public repository", 0.95)
        elif private is True:
            state.metadata_collector.collect("Platform API", f"{SDO}conditionsOfAccess", "Private repository", 0.95)
        return state
