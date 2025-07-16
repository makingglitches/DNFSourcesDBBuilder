INSERT INTO {generic} (
                          repo_uuid,
                          pkgid,
                          name,
                          version,
                          release_ver,
                          epoch,
                          flags
                      )
                      VALUES (
                          :repo_uuid,
                          :pkgid,
                          :name,
                          :version,
                          :release_ver,
                          :epoch,
                          :flags
                      );
