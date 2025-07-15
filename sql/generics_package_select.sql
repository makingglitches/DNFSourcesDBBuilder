
SELECT
       repo_uuid,
       pkgid,
       name,
       version,
       "release",
       epoch,
       flags
  FROM {generic}
  where pkgid=:pkgid and repo_uuid = :repo_uuid