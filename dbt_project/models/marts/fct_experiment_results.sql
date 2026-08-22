with base as (
    select
        experiment_id,
        variant,
        user_id,
        max(case when event_type = 'purchase' then 1 else 0 end) as converted,
        sum(case when event_type = 'purchase' then event_value else 0 end) as revenue
    from {{ ref('stg_events') }}
    group by 1, 2, 3
)

select
    experiment_id,
    variant,
    count(distinct user_id) as total_users,
    sum(converted) as total_conversions,
    round(sum(converted)::numeric / count(distinct user_id), 4) as conversion_rate,
    round(avg(revenue), 2) as avg_revenue_per_user
from base
group by 1, 2