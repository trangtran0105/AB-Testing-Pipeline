select
    event_id,
    user_id,
    experiment_id,
    variant,
    event_type,
    event_value,
    event_timestamp::timestamp as event_timestamp
from {{ source('raw', 'raw_events') }}