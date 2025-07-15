INSERT INTO repo (
                     repo_name,
                     repo_full_name,
                     repo_uuid,
                     primaryxmlfilename,
                     path,
                     is_source_repo
                 )
                 VALUES (
                     :repo_name,
                     :repo_full_name,
                     :repo_uuid,
                     :primaryxmlfilename,
                     :path,
                     :is_source_repo
                 );
