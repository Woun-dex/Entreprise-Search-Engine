from datetime import UTC, datetime
from pathlib import PurePosixPath
from uuid import UUID


class DiscoverGitHubFilesUseCase:

    def __init__(
        self,
        *,
        github: GitHubClient,
        connectors: ConnectorRepository,
        source_files: SourceFileRepository,
        file_policy: DocumentationFilePolicy,
    ) -> None:
        self._github = github
        self._connectors = connectors
        self._source_files = source_files
        self._file_policy = file_policy

    async def execute(
        self,
        connector_id: UUID,
    ) -> DiscoveryResult:
        connector = await self._connectors.get(connector_id)

        if connector is None:
            raise ValueError("Connector does not exist")

        if connector.status is not ConnectorStatus.ACTIVE:
            raise InvalidStateTransitionError(
                "Only active connectors can synchronize"
            )

        coordinates = parse_github_repository_url(
            connector.source_url
        )

        repository_info = await self._github.get_repository(
            owner=coordinates.owner,
            repository=coordinates.repository,
        )

        branch = (
            connector.branch_name
            or repository_info.default_branch
        )

        tree = await self._github.get_tree(
            owner=coordinates.owner,
            repository=coordinates.repository,
            ref=branch,
        )

        if tree.truncated:
            raise RepositoryTreeTruncatedError(
                "GitHub returned a truncated tree"
            )

        now = datetime.now(UTC)

        discovered_by_external_id: dict[
            str,
            DiscoveredGitHubFile,
        ] = {}

        for entry in tree.entries:
            if not self._file_policy.accepts(
                path=entry.path,
                size_bytes=entry.size_bytes,
                object_type=entry.object_type,
            ):
                continue

            discovered = DiscoveredGitHubFile(
                repository_id=repository_info.repository_id,
                owner=coordinates.owner,
                repository=coordinates.repository,
                branch=branch,
                path=entry.path,
                blob_sha=entry.sha,
                size_bytes=entry.size_bytes,
                source_url=(
                    f"https://github.com/"
                    f"{coordinates.owner}/"
                    f"{coordinates.repository}/blob/"
                    f"{branch}/{entry.path}"
                ),
            )

            discovered_by_external_id[
                discovered.external_id
            ] = discovered

        existing_files = await self._source_files.list_for_connector(
            connector_id
        )

        existing_by_external_id = {
            file.external_id: file
            for file in existing_files
            if file.status is not FileStatus.DELETED
        }

        created: list[SourceFile] = []
        updated: list[SourceFile] = []
        unchanged: list[SourceFile] = []
        deleted: list[SourceFile] = []

        for external_id, discovered in (
            discovered_by_external_id.items()
        ):
            existing = existing_by_external_id.get(external_id)

            if existing is None:
                source_file = SourceFile(
                    connector_id=connector.id,
                    external_id=external_id,
                    file_path=discovered.path,
                    file_name=PurePosixPath(
                        discovered.path
                    ).name,
                    source_version=discovered.blob_sha,
                    discovered_at=now,
                    size_bytes=discovered.size_bytes,
                    source_url=discovered.source_url,
                    allowed_principals=(
                        Principal("group:engineering"),
                    ),
                )

                await self._source_files.save(source_file)
                created.append(source_file)
                continue

            if existing.has_same_version(
                discovered.blob_sha
            ):
                existing.discovered_at = now
                existing.size_bytes = discovered.size_bytes
                existing.source_url = discovered.source_url

                await self._source_files.save(existing)
                unchanged.append(existing)
                continue

            existing.update_source_version(
                new_version=discovered.blob_sha,
                discovered_at=now,
            )

            existing.size_bytes = discovered.size_bytes
            existing.source_url = discovered.source_url

            await self._source_files.save(existing)
            updated.append(existing)

        current_ids = set(discovered_by_external_id)

        for external_id, existing in existing_by_external_id.items():
            if external_id in current_ids:
                continue

            existing.mark_deleted(now)
            await self._source_files.save(existing)
            deleted.append(existing)

        connector.mark_sync_succeeded(
            source_revision=tree.commit_sha,
            completed_at=now,
        )

        await self._connectors.save(connector)

        return DiscoveryResult(
            created=tuple(created),
            updated=tuple(updated),
            unchanged=tuple(unchanged),
            deleted=tuple(deleted),
            source_revision=tree.commit_sha,
        )