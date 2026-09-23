# X Home Timeline Algorithm — Exact Mechanics (from xai-org/x-algorithm, main)

Source repo: https://github.com/xai-org/x-algorithm (branch `main`, tree sha `1b3fec20bc3fd9879bc3e9f3d9c42753cdc3fede`)
Fetch method: raw.githubusercontent.com (HTTP 200). All values below are verbatim from the files.
Local mirror of fetched raw files: `/tmp/xalgo/` (flat names, e.g. `home-mixer_params_param.rs`).

---

## 1. ALL action weights — `home-mixer/params/param.rs`

File header (line 1): `// mirrored from config feature-switch defaults; last sync 2026-09-22T17:39:32Z`

Macro form: `param!(<RustName>, <Type>, "<feature switch key>", <default>);` — the **default** is the
effective weight when no experiment override is set. The feature-switch key is what an experiment
would override (e.g. `rust_home_mixer_favorite_weight`).

### 1.1 Positive / engagement weights (verbatim defaults)

| Weight name (Rust) | Feature-switch key | Default | Notes |
|---|---|---|---|
| `FavoriteWeight` | `rust_home_mixer_favorite_weight` | **0.5** | like |
| `ReplyWeight` | `rust_home_mixer_reply_weight` | **5.0** | |
| `BidirectionalFollowReplyWeightBoost` | `rust_home_mixer_bidirectional_follow_reply_weight_boost` | **15.0** | additive on reply weight for mutual-follow authors, original posts only |
| `BidirectionalFollowDwellWeightBoost` | `rust_home_mixer_bidirectional_follow_dwell_weight_boost` | **0.0** | currently OFF |
| `RetweetWeight` | `rust_home_mixer_retweet_weight` | **1.0** | |
| `PhotoExpandWeight` | `rust_home_mixer_photo_expand_weight` | **0.05** | |
| `VideoOpenWeight` | `rust_home_mixer_video_open_weight` | **0.07** | |
| `ClickWeight` | `rust_home_mixer_click_weight` | **0.4** | |
| `OpenLinkWeight` | `rust_home_mixer_open_link_weight` | **0.2** | |
| `ProfileClickWeight` | `rust_home_mixer_profile_click_weight` | **0.0** | |
| `VqvWeight` | `rust_home_mixer_vqv_weight` | **0.0** | video quality view |
| `ShareWeight` | `rust_home_mixer_share_weight` | **2.0** | |
| `ShareViaDmWeight` | `rust_home_mixer_share_via_dm_weight` | **5.0** | |
| `ShareViaCopyLinkWeight` | `rust_home_mixer_share_via_copy_link_weight` | **20.0** | highest positive weight |
| `DwellWeight` | `rust_home_mixer_dwell_weight` | **0.05** | binary "dwelled" prediction |
| `QuoteWeight` | `rust_home_mixer_quote_weight` | **5.0** | |
| `QuotedClickWeight` | `rust_home_mixer_quoted_click_weight` | **0.05** | |
| `QuotedVqvWeight` | `rust_home_mixer_quoted_vqv_weight` | **0.0** | |
| `FollowAuthorWeight` | `rust_home_mixer_follow_author_weight` | **4.0** | |
| `PostUnexploredWeight` | `rust_home_mixer_post_unexplored_weight` | **0.02** | additive by default; `PostUnexploredWeightInNetworkOnly`=true |
| `ContDwellTimeWeight` | `rust_home_mixer_cont_dwell_time_weight` | **0.004** | **continuous** action (predicted dwell seconds) |
| `ContClickDwellTimeWeight` | `rust_home_mixer_cont_click_dwell_time_weight` | **0.0** | continuous |
| `ContActiveSecs5mResidualNormWeight` | `rust_home_mixer_cont_active_secs_5m_residual_norm_weight` | **0.0** | continuous |

### 1.2 Negative weights (verbatim defaults)

| Weight name | Feature-switch key | Default |
|---|---|---|
| `NotInterestedWeight` | `rust_home_mixer_not_interested_weight` | **-43.2** |
| `BlockAuthorWeight` | `rust_home_mixer_block_author_weight` | **-31.2** |
| `MuteAuthorWeight` | `rust_home_mixer_mute_author_weight` | **-58.8** |
| `ReportWeight` | `rust_home_mixer_report_weight` | **-234.0** |
| `NotDwelledWeight` | `rust_home_mixer_not_dwelled_weight` | **-0.02** |

### 1.3 The "these weights do NOT mean what you think" comment (param.rs lines 321–349, duplicated at
`home-mixer/scorers/ranking_scorer.rs` lines 339–367)

> "These weights reflect a combination of how much an action is valued in ranking and typical
> propensities of these actions across the X network (e.g. negative feedback is overall rare)."
>
> "Each weight multiplies the *predicted* probability of that action (P(favorite), P(repost), …) or a
> continuous value e.g. watch time -- the weights do not multiply raw engagement counts. One common
> misinterpretation is that you can read these weight ratios as count equivalences, e.g. the incorrect
> statement that "one report cancels 468 likes" -- this is incorrect because the weights apply to the
> predicted probabilities rather than raw counts."
>
> "And the baseline probability of a Report is more than 1000x lower than a Like, so it's weighted more
> to allow the prediction to affect the final ranking at all."
>
> "Related to the above is a misunderstanding that bad actors engaging in mass blocking/reporting will
> significantly suppress reach. There are multiple things inhibiting this: 1. It's predicting your
> likelihood of the action, not summing up raw weights on counts. Also, recommendations are
> personalized, so reports from bad actors will primarily affect recommendations for users who are
> similar to the bad actors, rather than having the same effect on the post's ranking to everyone.
> 2. For an account to count in the algorithms recommendation system, it must take place on a post
> served in Home Timeline. Directly navigating to a post (i.e., coordinating via groupchat) has no
> ranking impact. And users cannot manufacture a post to show up in their Timeline in any consistently
> reproducible way."

**Implication for us:** the report/like ratio (468 = 234/0.5) is a red herring; the only thing that
moves ranking is the *model's predicted probability* for the viewer, and only impressions served in
Home Timeline count at all (matching the payout definition: unique Premium Home-Timeline impressions).

### 1.4 Other numeric params relevant to distribution (same file)

| Param | Default | Meaning |
|---|---|---|
| `EnableRanking` | true | |
| `EnableAuthorDiversity` | true | |
| `AuthorDiversityDecay` | **0.5** | |
| `AuthorDiversityFloor` | **0.25** | |
| `OonWeightFactor` | **0.75** | out-of-network multiplier |
| `TopicOonWeightFactor` | **0.5** | OON multiplier when topic_ids non-empty |
| `NewUserAgeThresholdSecs` | **0** | |
| `NewUserOonWeightFactor` | **0.00001** | |
| `EnableOonRescoreForInNetworkRepliesRetweets` | true | in-network replies/retweets ALSO get OON discount |
| `MultiplierPreOffset` | false | if true, diversity+OON applied before the negative-score offset |
| `EnableMultiplicativePostUnexplored` | false | |
| `MultiplicativePostUnexploredAlpha` | 0.0 | |
| `PostUnexploredWeightInNetworkOnly` | true | post_unexplored term only for in-network candidates |
| `EnableCdwellOnImpr` | false | if true, click-dwell term = click_dwell_time × click_score |
| `MinVideoDurationMs` | 10_000 | vqv weight gated on video length ≥10s |
| `EnableQuotedVqvDurationCheck` | false | |
| `WeightPerturbationSigma` | 0.0 | per-user random weight perturbation (A/B noise) |
| `ColdStartImpressionThreshold` | **1000** | author cold-start boost applies below this impression count |
| `ColdStartSlotMin` | **15** | |
| `ColdStartSlotMax` | **16** | target insertion slot window |
| `ColdStartFollowerCap` | **1000** | author must have ≤1000 followers |
| `ColdStartMaxPostAgeSecs` | **172800** | = 48 h |
| `LowImpressionsMaxPositionRatio` | **0.85** | boost cannot go deeper than 85% of the slate |
| `EnableViewerColdStart` | true | |
| `EnableColdStartThompsonSampling` | false | |
| `ColdStartBetaAlpha0` / `ColdStartBetaBeta0` | 0.75 / 49.25 | Beta prior for Thompson sampling |
| `ColdStartTsTopK` | 2 | |
| `SimclustersMaxCandidateAgeHours` | **48** | candidate source age cap |
| `ExcludeServedTweetIdsDuration` | 10 (minutes) | |
| `ExcludeServedTweetIdsNumber` | 100 | |
| `EngagementSignalsMaxPerType` | 15 | |
| `PhoenixScoresResultSize` | 2800 | |
| `PhoenixMaxResults` | 1000 | |
| `ThunderMaxResults` | 1200 | |
| `MaxPostsToCache` | 750 | |
| `UseEngagementCounterViewCountForImpressionBoost` | true | view_count feeds cold-start reward |

`home-mixer/params/config.rs` constants:
```rust
pub const MAX_POST_AGE: u64 = 48 * 60 * 60;          // 48h hard age cap
pub const TOP_K_CANDIDATES_TO_SELECT: usize = 50;
pub const RESULT_SIZE: usize = 35;
pub const FEED_MODULE_SLOTS: usize = 4;
pub const FOR_YOU_MAX_RESULT_SIZE: usize = RESULT_SIZE + FEED_MODULE_SLOTS + MAX_JETFUEL_FRAMES_PER_RESPONSE; // 35+4+8 = 47
pub const NEGATIVE_SCORES_OFFSET: f64 = 0.001;
pub const NEW_USER_MIN_FOLLOWING: usize = 5;
pub const WHO_TO_FOLLOW_POSITION: usize = 6;
```

---

## 2. How RankingScorer combines scores — `home-mixer/scorers/ranking_scorer.rs`

### 2.1 The weighted-sum formula

`RankingScorer::compute_weighted_parts` (line 381) builds a flat array of terms and splits them into
positive and negative sums (lines 463–472):

```rust
let mut pos = 0.0;
let mut neg = 0.0;
for t in terms {
    if t >= 0.0 { pos += t; } else { neg -= t; }
}
(pos, neg)
```

and `compute_weighted_score` (line 372) returns `Self::offset_score(pos - neg, weights)`.

Each term is `score.unwrap_or(0.0) * weight` (line 368–370):

```rust
fn apply(score: Option<f64>, weight: f64) -> f64 {
    score.unwrap_or(0.0) * weight
}
```

So: **score = Σ (predicted_probability_or_continuous_value × weight)**, missing predictions count as 0.

### 2.2 The exact term list, in code order (lines 421–461)

```
favorite_score            × favorite (0.5)
reply_score               × reply_weight_for(candidate)   // 5.0, +15.0 if bidirectional boost eligible
retweet_score             × retweet (1.0)
photo_expand_score        × photo_expand (0.05)
video_open_score          × video_open (0.07)
click_score               × click (0.4)
open_link_score           × open_link (0.2)
profile_click_score       × profile_click (0.0)
vqv_score                 × vqv_weight  (0.0 default, gated on MinVideoDurationMs)
share_score               × share (2.0)
share_via_dm_score        × share_via_dm (5.0)
share_via_copy_link_score × share_via_copy_link (20.0)
dwell_score               × dwell_weight_for(candidate)   // 0.05
quote_score               × quote (5.0)
quoted_click_score        × quoted_click (0.05)
quoted_vqv_score          × quoted_vqv_weight (0.0)
dwell_time_term           ← CONTINUOUS
click_dwell_term(scores)  × cont_click_dwell_time (0.0)   ← CONTINUOUS
active_secs_5m_residual_norm × cont_active_secs_5m_residual_norm (0.0) ← CONTINUOUS
follow_author_score       × follow_author (4.0)
not_interested_score      × not_interested (-43.2)
block_author_score        × block_author (-31.2)
mute_author_score         × mute_author (-58.8)
report_score              × report (-234.0)
not_dwelled_score         × not_dwelled (-0.02)
post_unexplored_term      (0.0 if EnableMultiplicativePostUnexplored else post_unexplored_score × 0.02)
```

### 2.3 Continuous actions (dwell time, video watch)

Continuous terms use the same `apply()` but the score is a predicted continuous value (seconds), not a
probability (lines 404–413):

```rust
let base_dwell_time_term = Self::apply(scores.dwell_time, weights.cont_dwell_time);
let dwell_time_term = match scores.post_unexplored_score {
    Some(post_unexplored)
        if weights.enable_multiplicative_post_unexplored && post_unexplored_active =>
    {
        base_dwell_time_term
            * (1.0 + post_unexplored * weights.multiplicative_post_unexplored_alpha)
    }
    _ => base_dwell_time_term,
};
```

`ContDwellTimeWeight = 0.004` is per **second** of predicted dwell. `click_dwell_time` is multiplied by
`ContClickDwellTimeWeight = 0.0` (off) and, if `EnableCdwellOnImpr` were true, would be
`click_dwell_time × click_score` (lines 243–252). `active_secs_5m_residual_norm` weight is 0.0 (off).

Video: `vqv` weight is 0.0 by default and `vqv_weight(...)` gates on `MinVideoDurationMs = 10_000`
(videos under 10 s get no vqv credit). `video_open` (0.07) and `photo_expand` (0.05) are live but tiny.

### 2.4 Negative-score offset (lines 475–483)

```rust
pub(crate) fn offset_score(combined_score: f64, w: &ScoringWeights) -> f64 {
    if w.total_sum == 0.0 {
        combined_score.max(0.0)
    } else if combined_score < 0.0 {
        (combined_score + w.negative_sum) / w.total_sum * NEGATIVE_SCORES_OFFSET
    } else {
        combined_score + NEGATIVE_SCORES_OFFSET
    }
}
```

with `NEGATIVE_SCORES_OFFSET = 0.001` (config.rs). `negative_sum = -(not_interested + block_author +
mute_author + report + not_dwelled)` and `total_sum = positive_sum + negative_sum` (lines 158–163).
Effect: non-negative scores are shifted by +0.001; net-negative scores are compressed into (0, 0.001)
— so a post whose net weighted score is negative is always ranked below every post with a positive net
score, but is not removed.

### 2.5 Pipeline order of adjustments in `score()` (lines 582–699)

Default path (`MultiplierPreOffset = false`):
1. `weighted_scores` = offset applied per candidate.
2. **Author cold-start lift** applied to `weighted_scores` → `adjusted_scores`
   (`self.author_cold_start.apply_with_decisions(query, candidates, &weighted_scores)`).
3. **Author diversity**: `apply_author_diversity(...)` multiplies by the diversity multiplier.
4. **OON discount**: `if oon_applies(c) { after_diversity * effective_oon }`.

If `MultiplierPreOffset = true`, diversity and OON are applied to the *unoffset* net score, then
re-offset, and cold start is applied after — the order is explicitly a feature-switchable experiment.

### 2.6 Author Diversity (lines 499–552)

```rust
fn diversity_multiplier(decay_factor: f64, floor: f64, exponent: f64) -> f64 {
    (1.0 - floor) * decay_factor.powf(exponent) + floor
}
```

- `AuthorDiversityDecay = 0.5`, `AuthorDiversityFloor = 0.25` (param.rs lines 264–275).
- `exponent` = k = how many of that author's posts are already ranked **above** this one in the slate
  (`author_pool_counts`, lines 503–520 — counts assigned in descending pre-diversity score order).
- Multiplier by k: k=0 → 1.0; k=1 → 0.625; k=2 → 0.4375; k=3 → 0.34375; floor → 0.25.
- Test at line 764 (`applies_author_diversity_decay_in_score_order`) asserts exactly this.

### 2.7 Out-of-Network discount (lines 554–573, 599–610, 671–682)

```rust
fn effective_oon_weight(query: &ScoredPostsQuery) -> f64 {
    if !query.topic_ids.is_empty() {
        return query.params.get(TopicOonWeightFactor);      // 0.5
    }
    let oon_weight_factor = query.params.get(OonWeightFactor);  // 0.75
    ...
    if is_eligible_new_user { query.params.get(NewUserOonWeightFactor) }  // 0.00001
    else { oon_weight_factor }
}
```

- **`OonWeightFactor = 0.75`** — every out-of-network candidate's score is multiplied by 0.75.
- `TopicOonWeightFactor = 0.5` when the request carries topic ids.
- `NewUserOonWeightFactor = 0.00001` for new users — but `NewUserAgeThresholdSecs = 0` by default,
  and eligibility also requires `followed_user_ids.len() >= NEW_USER_MIN_FOLLOWING` (5).

`oon_applies` (lines 603–610) — **critical detail**: the discount applies to `in_network == Some(false)`
**and also to in-network replies and retweets**, because
`EnableOonRescoreForInNetworkRepliesRetweets = true` by default:

```rust
let oon_applies = |c: &PostCandidate| match c.in_network {
    Some(false) => true,
    Some(true) => {
        deboost_in_network_replies_retweets
            && (c.in_reply_to_tweet_id.is_some() || c.retweeted_tweet_id.is_some())
    }
    None => false,
};
```

i.e. **in-network ORIGINAL posts are never OON-discounted; in-network replies and retweets are.**

---

## 3. New-Author / Cold-Start Boost — `home-mixer/scorers/author_cold_start.rs`

This is the "new author boost" mechanism. Params read in `ColdStartParams::read` (lines 62–79).

Eligibility for a boosted slot (`cold_start_base_eligible`, line 171 + filter at lines 301–313):

```rust
pub(crate) fn cold_start_base_eligible(c: &PostCandidate, follower_cap: i64) -> bool {
    c.in_reply_to_tweet_id.is_none()
        && c.retweeted_tweet_id.is_none()
        && c.author_followers_count
            .is_some_and(|followers| (followers as i64) <= follower_cap)
}
```

plus all of:
- `duration_since_creation_opt(c.tweet_id) <= params.max_post_age` → **`ColdStartMaxPostAgeSecs = 172800` (48 h)**
- `positions[i] < max_cold_start_slot` where `max_cold_start_slot = (LowImpressionsMaxPositionRatio * nonzero) as usize`
  → **`LowImpressionsMaxPositionRatio = 0.85`** (boost only reaches into the top 85 % of the slate)
- `c.view_count_on_home < params.impression_threshold` → **`ColdStartImpressionThreshold = 1000`**
  (post must have < 1000 Home-Timeline impressions so far)
- follower cap: **`ColdStartFollowerCap = 1000`** followers max
- **original posts only** — no replies, no retweets

**Target position** (`cold_start_target`, lines 220–230):

```rust
let hi = params.slot_max.min(ranked.len());
let lo = params.slot_min.min(hi);
if lo >= hi { return None; }
let rank = rand::rng().random_range(lo..hi);
Some((rank, ranked[rank]))
```

with **`ColdStartSlotMin = 15`, `ColdStartSlotMax = 16`** → the boost target is a *random rank in
[15, 16)* i.e. slot 15 (0-indexed) — approximately position 16 in the slate. The chosen post's score is
raised to the score of the post currently at that rank (`effective[best_idx] = effective[best_idx].max(target)`),
and only ONE post per request is lifted (`record_cold_started_posts(..., 1)`).

Selection among eligible posts: highest score, or Thompson sampling over
Beta(alpha0 + favs, beta0 + impressions − favs) with `ColdStartBetaAlpha0 = 0.75`,
`ColdStartBetaBeta0 = 49.25`, `ColdStartTsTopK = 2`, `ColdStartImpressionScale = 1.0` when
`EnableColdStartThompsonSampling` is on (it is **false** by default) — lines 247–287.

Master switch: **`EnableViewerColdStart = true`** (`rust_home_mixer_enable_viewer_cold_start_boost`).
Also note `is_phoenix_moe(c)` candidates are zeroed unless the viewer arm is Treatment and the author
corpus is Treatment (lines 199–218) — a separate MoE codivert experiment.

**Implication for a 279-follower account:** you qualify on every dimension (≤1000 followers, original
posts, <48 h old, <1000 impressions on that post). You get at most ONE lifted post per request,
targeted around slot 15–16 — i.e. roughly one guaranteed appearance in the upper-middle of the For You
slate per session where the post is under the impression threshold. This is the single biggest
algorithmic lever for a small account, and it stops applying once a post crosses 1000 impressions.

---

## 4. Pre-scoring filters — `home-mixer/filters/`, wired with `home-mixer/params/config.rs`

README (`README.md` lines 361–385) gives the exact list **in order**:

| Filter | Removes |
|---|---|
| `DropDuplicatesFilter` | The same post returned by more than one source |
| `CoreDataHydrationFilter` | Posts whose text and metadata failed to load |
| **`AgeFilter`** | **Posts older than 48 hours** |
| `SelfTweetFilter` | The viewer's own posts |
| `OONRetweetReplyFilter` | Reposts and replies from accounts the viewer does not follow, and replies whose parent is missing |
| `OONNsfwSimclustersFilter` | SimClusters posts whose author is flagged for adult content, when the viewer does not follow them |
| `RetweetDeduplicationFilter` | Repeated reposts of the same post |
| `IneligibleSubscriptionFilter` | Subscriber-only posts the viewer cannot access |
| `PreviouslySeenPostsFilter` | Posts the viewer has already been shown |
| `PreviouslySeenPostsBackupFilter` | The same, from a second record of impressions |
| `PreviouslyServedPostsFilter` | Posts already served earlier in the session |
| `MutedKeywordFilter` | Posts matching the viewer's muted keywords |
| `AuthorSocialgraphFilter` | Posts from accounts the viewer blocks or mutes |
| `VideoFilter` | Video posts, when the request excludes video |
| `TopicIdsFilter` | Posts outside the requested topics, and posts in excluded topics |
| `NewUserMinEngagementFilter` | For new accounts, out-of-network posts below an engagement threshold |
| `InventoryHoldoutFilter` | A configured percentage of posts, chosen deterministically per post and viewer |

README line 385: *"Already-seen posts are handled twice over: `ThunderSource` is passed the list and
leaves them out, the other sources are not, so their repeats are caught by the filters above."*

Exact code:

- **48 h age cap** — `home-mixer/params/config.rs`: `pub const MAX_POST_AGE: u64 = 48 * 60 * 60;`
  and `home-mixer/filters/age_filter.rs`:
  ```rust
  fn is_within_age(&self, tweet_id: u64) -> bool {
      duration_since_creation_opt(tweet_id)
          .map(|age| age <= self.max_age)
          .unwrap_or(false)
  }
  ```
  Note `.unwrap_or(false)` — a post whose age cannot be derived is **removed**.

- **Already seen** — `home-mixer/filters/previously_seen_posts_filter.rs` partitions candidates on
  `related_post_ids_iter(c).any(|post_id| seen_ids.contains(&post_id) || bloom_filters.iter().any(|f| f.may_contain(post_id)))`
  → removed if the post, or any related post id (quoted/reposted ancestor), was seen. Bloom filters
  are queried too (probabilistic — can drop a post you have not literally seen).

- **Already served** — `previously_served_posts_filter.rs` removes anything whose id (or related id) is
  in `query.served_ids`. Enabled by default for all requests (`EnableServedFilterAllRequests = true`).
  Served-id memory window: `ExcludeServedTweetIdsDuration = 10` minutes, `ExcludeServedTweetIdsNumber = 100`.

- **Own posts** — `self_tweet_filter.rs` (viewer's own posts are excluded).

- **OON replies/reposts** — `home-mixer/filters/oon_retweet_reply_filter.rs`: reposts and replies from
  non-followed accounts are removed entirely from For You.

- **Muted keywords / blocks / mutes** — `viewer_muted_keyword_filter.rs`,
  `following_viewer_muted_keyword_filter.rs`, `author_socialgraph_filter.rs`.

- **Result size** — `config.rs`: `RESULT_SIZE = 35`, `FOR_YOU_MAX_RESULT_SIZE = 35 + 4 + 8 = 47`,
  `TOP_K_CANDIDATES_TO_SELECT = 50`.

### 4.1 In-code filter order — `home-mixer/candidate_pipeline/phoenix_candidate_pipeline.rs` lines 359–385

```rust
let filters: Vec<Box<dyn Filter<ScoredPostsQuery, PostCandidate>>> = vec![
    Box::new(DropDuplicatesFilter),
    Box::new(CoreDataHydrationFilter),
    Box::new(AgeFilter::new(Duration::from_secs(params::MAX_POST_AGE))),
    Box::new(SelfTweetFilter),
    Box::new(OONRetweetReplyFilter),
    Box::new(OONNsfwSimclustersFilter),
    Box::new(RetweetDeduplicationFilter),
    Box::new(IneligibleSubscriptionFilter),
    Box::new(PreviouslySeenPostsFilter),
    Box::new(PreviouslySeenPostsBackupFilter),
    Box::new(PreviouslyServedPostsFilter),
    Box::new(ViewerMutedKeywordFilter::new()),
    Box::new(AuthorSocialgraphFilter),
    // Brazil 2026 election filter
    Box::new(Brazil2026ElectionFilter),
    Box::new(VideoFilter),
    Box::new(TopicIdsFilter),
    Box::new(NewUserMinEngagementFilter),
    ...
```

Exact `OONRetweetReplyFilter` predicate (`home-mixer/filters/oon_retweet_reply_filter.rs` lines 13–18) —
the README's plain-English version is "reposts and replies from accounts the viewer does not follow":

```rust
let (removed, kept): (Vec<_>, Vec<_>) = candidates.into_iter().partition(|c| {
    let is_reply = c.in_reply_to_tweet_id.is_some();
    let is_retweet = c.retweeted_tweet_id.is_some();
    (c.in_network == Some(false) && (is_retweet || is_reply))
        || (is_reply && c.ancestors.is_empty())
});
```

i.e. **out-of-network retweets and replies are removed outright, and any reply whose ancestor chain
failed to hydrate is removed** — but in-network originals survive untouched.

The Brazil 2026 election filter is annotated in-code with its legal basis:
> "Application providers that use a recommendation system for users must exclude from the results the
> channels and profiles reported to the Electoral Court ... https://dadosabertos.tse.jus.br/dataset/candidatos-2026"

---

## 5. Visibility filtering — what causes a DROP

`visibility-filtering/` answers **ALLOW / INTERSTITIAL / DROP** per (post, viewer). README lines 204–220:

> "for each post and viewer, one of three answers: ALLOW show the post normally · INTERSTITIAL show it
> behind an interstitial the viewer can tap through, e.g. for adult or graphic media · DROP do not show it"
>
> "the rules read the labels above, plus whether the viewer blocks, mutes or follows the author, whether
> that account is protected, suspended or deactivated, subscriber-only status, and the viewer's settings
> and country. **Some rules drop a post only when it is a recommendation from an account the viewer does
> not follow — spam caught at high recall, for instance. The same post is allowed to a follower.**"

Post-selection enforcement: `home-mixer/filters/vf_filter.rs`:

```rust
pub(crate) fn should_drop_action(action: &Action) -> bool {
    match action {
        Action::Allow | Action::Interstitial | Action::Avoid | Action::Downrank => false,
        Action::Drop(_) | Action::Tombstone | Action::NotEvaluated => true,
    }
}
```

**`NotEvaluated` is treated as a drop** — if visibility filtering fails to answer for a post, it is
removed. And `ancillary_vf_filter.rs` removes posts whose ancestor/quoted/reposted post was dropped
(`drop_ancillary_posts`). README lines 222–230: *"drop ──► the post is removed after ranking, and so is
any post whose ancestor in the thread, quoted post or reposted post was itself dropped"*.

### 5.1 Rule groups that run for Home Timeline (`visibility-filtering/rules/registry.rs` lines 125–150)

```rust
static TIMELINE_HOME_SHARED_RULES: [&[RuleClause]; 10] = [
    author_rules::AUTHOR_STATE_DROPS,
    author_rules::SOCIALGRAPH_DROPS,
    tweet_rules::TWEET_LABEL_DROPS,
    tweet_rules::NULLCAST_DROP,
    tweet_rules::STALE_TWEET_DROP,
    tweet_rules::TAKEDOWN_DROPS,
    tweet_rules::SENSITIVE_VIEWER_DROPS,
    tweet_rules::EXCLUSIVE_TWEET_DROP,
    tweet_rules::NSFW_MEDIA_INTERSTITIALS,
    tweet_rules::NSFW_AUTHOR_INTERSTITIAL,
];

static TIMELINE_HOME_RECOMMENDATION_ONLY_RULES: [&[RuleClause]; 5] = [
    tweet_rules::RECS_MEDIA_DROPS,
    author_rules::OON_NSFW_AUTHOR_DROPS,
    tweet_rules::OON_TWEET_FLAG_DROPS,
    tweet_rules::OON_TWEET_LABEL_DROPS,
    author_rules::OON_USER_LABEL_DROPS,
];
```

README line 399: *"The first rule that answers drop ends the evaluation."* and line 400: *"A further set
of rules applies only when the post is a recommendation from an account the viewer does not follow, and
those rules can only drop ... The same post is allowed to a follower."*

### 5.2 Post-level labels that cause a DROP (`visibility-filtering/rules/tweet_rules.rs`, `TWEET_LABEL_DROPS`)

| Rule | Label / predicate | Action |
|---|---|---|
| `PdnaTweetLabelRule` | `SafetyLabelType::PDNA` | Drop |
| `BounceTweetLabelRule` | `BOUNCE` | Drop (`TweetIsBounced`) |
| `SpamTweetLabelRule` | `SPAM` | Drop (`PossiblyUndesirable`) |
| `ForEmergencyUseOnlyDropRule` | `FOR_EMERGENCY_USE_ONLY` | Drop |
| `FosnrHatefulConductDropRule` | `FOSNR_HATEFUL_CONDUCT` | Drop |
| `FosnrViolentSpeechDropRule` | `FOSNR_VIOLENT_SPEECH` | Drop |
| `FosnrAbuseDropRule` | `FOSNR_ABUSE` | Drop |
| `FosnrCivicIntegrityDropRule` | `FOSNR_CIVIC_INTEGRITY` | Drop |

OON-only post drops (`OON_TWEET_LABEL_DROPS`) — apply when the viewer does not follow the author:
`NSFW_HIGH_RECALL`, `NSFW_HIGH_PRECISION`, `GORE_AND_VIOLENCE_HIGH_PRECISION`, `NSFW_CARD_IMAGE`,
**`DO_NOT_AMPLIFY`**, **`MALICIOUS_URL`**, **`SPAM_HIGH_RECALL`**, `NSFW_TEXT`, `FOSNR_ABUSE_INSULTS`.
Plus `OON_TWEET_FLAG_DROPS` (`NsfwUserFlag`, `NsfwAdminFlag`) and `RECS_MEDIA_DROPS`
(`HasDmcaMedia`), and `NULLCAST_DROP` (nullcasted posts), `STALE_TWEET_DROP` (superseded edits).

### 5.3 Author-level labels that cause a DROP (`visibility-filtering/rules/author_rules.rs`)

`AUTHOR_STATE_DROPS`: `IsSuspended`, `IsDeactivated`, `IsErased`, `IsOffboarded`, `IsProtected`
(protected only drops for non-followers).

`OON_USER_LABEL_DROPS` (recommendation-only; audience `ExceptAuthor`, some `ExceptAuthorAndFollowers`):
`NsfwHighRecall`, `NsfwHighPrecision`, `SpamHighRecall`, `Compromised`, `ReadOnly`,
`ImpersonationHighPrecision`, `NsfwAvatarImage`, `NsfwBannerImage`, `AbusiveHighRecall` (ExceptAuthorAndFollowers),
`NsfwNearPerfect`, **`DoNotAmplify`** (ExceptAuthorAndFollowers).

`SOCIALGRAPH_DROPS`: `ViewerBlocksAuthorRule`, `ViewerMutesAuthorRule`, `MutedRetweetsRule`.

Also `NSFW_MEDIA_INTERSTITIALS` / `NSFW_AUTHOR_INTERSTITIAL` → **Interstitial, not Drop** (post stays in
the feed); `EXCLUSIVE_TWEET_DROP` → Drop for subscriber-only content the viewer cannot access;
`SENSITIVE_VIEWER_DROPS` → Drop for logged-out/underage viewers when NSFW labels present;
`TAKEDOWN_DROPS` → `legal_takedown_in_viewer_country` (compliance takedowns).

**Key structural takeaway:** for an original post from an account the viewer *follows*, the only labels
that can drop it are `PDNA`, `BOUNCE`, `SPAM`, `FOR_EMERGENCY_USE_ONLY`, the four `FOSNR_*` labels,
exclusive-content, legal takedowns, and author-state labels. The high-recall spam/NSFW/malicious-URL
labels only bite **out-of-network**. That is why "the same post is allowed to a follower."

---

## 6. Comments about what maximizes distribution (direct quotes)

1. **Ranking ≠ visibility.** README line 74: *"Ranking sets the order. Whether a post can be shown at
   all is decided separately, by `visibility-filtering/`, from the viewer's own actions such as blocks
   and mutes and from labels that other systems here attach to posts and accounts."*
   README line 472 (Key Design Decisions #4): *"Ranking and Visibility Are Separate."*

2. **The weights multiply predictions, not counts** (param.rs 321–335, README line 349). The only path
   to impressions is raising the viewer's *predicted* probability of taking positive actions —
   which is "substantially driven by your own behavior" per the README, i.e. by how your existing
   audience actually engages.

3. **Only Home-Timeline-served actions count** (param.rs 345–349): *"For an account to count in the
   algorithms recommendation system, it must take place on a post served in Home Timeline. Directly
   navigating to a post (i.e., coordinating via groupchat) has no ranking impact. And users cannot
   manufacture a post to show up in their Timeline in any consistently reproducible way."*

4. **Mass reporting/blocking does not suppress reach** (param.rs 337–344): personalized recommendations
   mean hostile reports mainly affect *similar* viewers, not everyone.

5. **Candidate isolation** (README line 464): *"During transformer inference, candidates cannot attend
   to each other—only to the viewer context. This ensures the score for a post doesn't depend on which
   other posts are in the batch, making scores consistent and cacheable."* → your post's predicted
   action probabilities do not depend on which other posts it competes with; only the final ordering
   and the diversity/OON/cold-start multipliers do.

6. **Hash-based embeddings** (README line 468): *"a new post is representable immediately"* — no
   cold-start penalty from vocabulary/embedding coverage.

7. **What's not published** (README lines 418–433): Grox LLM prompts and some botmaker rules are
   withheld *"to reduce the risk of gaming to circumvent these systems"*. So exact spam-classifier
   thresholds are not knowable from the repo; the Under the Hood tool (`x.com/i/under_the_hood`) shows
   your own applied labels.

---

## 7. Top implications for maximizing Home-Timeline impressions (279-follower account)

1. **Post originals, not replies/reposts — it is mechanically enforced.** `oon_applies` discounts
   in-network **replies and retweets** by 0.75 while in-network originals are never discounted
   (ranking_scorer.rs 603–610), and `OONRetweetReplyFilter` deletes non-followed accounts'
   replies/reposts before scoring. The cold-start boost is also originals-only
   (`in_reply_to_tweet_id.is_none() && retweeted_tweet_id.is_none()`). Reposts/replies are structurally
   the worst-distributed content type on For You.

2. **Farm the New-Author Boost deliberately.** With ≤1000 followers, <48 h post age, and <1000
   impressions on the post, one of your posts is lifted to ~slot 15–16 per request
   (`ColdStartSlotMin=15`, `ColdStartSlotMax=16`, `ColdStartImpressionThreshold=1000`,
   `ColdStartFollowerCap=1000`, `LowImpressionsMaxPositionRatio=0.85`). It only applies while the post
   is *under* 1000 impressions, so **spread posts out** rather than posting several at once — a second
   post in the same window competes for the single lift per request. Get each post its first ~1000
   impressions before the next one.

3. **Optimize for `reply` (5.0), `share_via_copy_link` (20.0), `share_via_dm` (5.0), `quote` (5.0),
   `follow_author` (4.0)** — these are the highest live weights, and they are predictions, so content
   that reliably provokes *replies and link-copies* from the viewers who already see you is what grows
   the score. `favorite` is only 0.5 and `dwell` 0.05; `cont_dwell_time` is 0.004/second. A like is
   cheap; a reply or a copy-link share is worth 10–40 likes in weight terms (though not in count terms).
   `vqv` and `profile_click` are 0.0 — video quality views and profile clicks are currently worthless
   for ranking, so do not optimize for them.

4. **Avoid all negative feedback — it dominates everything.** `report` = −234, `mute_author` = −58.8,
   `not_interested` = −43.2, `block_author` = −31.2, versus `favorite` = +0.5. One predicted report
   swamps 468 likes' worth of weight. Any net-negative post is pushed below *every* positive-net post
   by the `offset_score` compression into (0, 0.001). Zero-tolerance content policy: nothing that
   provokes "Not interested", mutes, blocks or reports, even from a minority of viewers.

5. **Do not get labeled — and note that OON is where labels bite.** Out-of-network reach (the only way
   to grow past your followers) is discounted ×0.75 and additionally subject to `OON_TWEET_LABEL_DROPS`
   (`SPAM_HIGH_RECALL`, `DO_NOT_AMPLIFY`, `MALICIOUS_URL`, `NSFW_*`) and `OON_USER_LABEL_DROPS`
   (`SpamHighRecall`, `AbusiveHighRecall`, `DoNotAmplify`, ...). A `DO_NOT_AMPLIFY` or `SpamHighRecall`
   label silently kills all non-follower distribution while followers still see you — the classic
   "my reach fell off a cliff" signature. Check `x.com/i/under_the_hood` and keep link behaviour clean
   (no malicious/redirect URLs — `MaliciousUrlOonDropRule`).

6. **(Bonus) Diversity and timing.** Your own posts compete with each other: the k-th post from the
   same author in a slate is multiplied by `(1−0.25)·0.5^k + 0.25` → 1.0, 0.625, 0.4375, 0.34375 …
   (floor 0.25). And a post is dead after 48 h (`MAX_POST_AGE`, `SimclustersMaxCandidateAgeHours=48`,
   `ColdStartMaxPostAgeSecs=172800`) — so cadence matters: publish frequently enough to always have a
   fresh (<48 h) candidate for retrieval, but not so often that your posts cannibalize each other's
   slots and the single cold-start lift.

