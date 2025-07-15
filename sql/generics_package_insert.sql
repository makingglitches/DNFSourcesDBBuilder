INSERT INTO {generic} (
                          repo_uuid,
                          pkgid,
                          name,
                          version,
                          [release],
                          epoch,
                          flags
                      )
                      VALUES (
                          :repo_uuid,
                          :pkgid,
                          :name,
                          :version,
                          :release,
                          :epoch,
                          :flags
                      );
