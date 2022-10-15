CREATE KEYSPACE IF NOT EXISTS twitter WITH replication = {'class':'SimpleStrategy','replication_factor':'1'};

CREATE TABLE twitter.tweets (day int,
                            hour smallint,
                            minute smallint,
                            ms int,
                            datacenterid int,
                            serverid int,
                            sequenceid int,
                            id bigint,
                            crawled_timestamp timestamp,
                            user_name text,
                            user_displayname text,
                            user_id bigint,
                            user_verified boolean,
                            user_description text,
                            user_created timestamp,
                            user_favourites_count int,
                            user_friends_count int,
                            user_followers_count int,
                            user_statuses_count int,
                            user_protected boolean,
                            reply_to_id bigint,
                            reply_to_user text,
                            reply_to_user_id bigint,
                            truncated boolean,
                            hashtags set<text>,
                            cashtags set<text>,
                            urls set<text>,
                            user_mentions set<text>,
                            text text,

                            hearts_count int,
                            retweets_count int,
                            quoted_status_id bigint,
                            possibly_sensitive boolean,
                            language text,
                            download_source smallint,
                            download_status smallint,
                            has_media boolean,

                            PRIMARY KEY ((day, hour, minute), ms, datacenterid, serverid, sequenceid) )
                            WITH CLUSTERING ORDER BY (ms DESC);

// CREATE INDEX username_idx on twitter.tweets (user_name);
// CREATE INDEX userid_idx on twitter.tweets (user_id);
// CREATE INDEX snowflake_idx on twitter.tweets (id);



// For later use, ignore for now
/* CREATE TABLE twitter.users (user_id bigint,
                            name text,
                            screen_name text,
                            location text,
                            url text,
                            description text,
                            protected boolean,
                            crawled timestamp,
                            followers_count int,
                            friends_count int,
                            listed_count int,
                            favorites_count int,
                            statuses_count int,
                            language text,
                            contributors_enabled boolean,
                            profile_image_url text,
                            withheld_in_countries text,
                            PRIMARY KEY(user_id, followers_count)); */