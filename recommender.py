# Tag-based recommendation model fed by Cloudinary's AI-generated tags.
#
# The model is intentionally simple and dependency-free: the tags that Amazon
# Rekognition (aws_rek_tagging) attached at upload time are the features, the
# selected products define a tag-frequency profile, and every other product is
# scored by how strongly its tags overlap with that profile.

from collections import Counter

# Tags that carry no signal for recommendations: "my_products" is on every
# asset, and "adult" is a Rekognition label that matches most fashion photos.
IGNORED_TAGS = frozenset({"adult", "my_products"})

# How many of the most frequent tags in the selection are used for matching.
TOP_TAGS = 3


def clean_tags(tags):
    """Return the meaningful tags of an asset, lower-cased and de-duplicated."""
    seen = []
    for tag in tags or []:
        tag = str(tag).strip().lower()
        if tag and tag not in IGNORED_TAGS and tag not in seen:
            seen.append(tag)
    return seen


def most_frequent(tag_list, n=TOP_TAGS):
    """Return the n most common tags as (tag, count) pairs."""
    return Counter(tag_list).most_common(n)


def build_profile(selected_ids, catalog, top_n=TOP_TAGS):
    """Build the tag profile (most frequent tags) of the selected products."""
    by_id = {asset["public_id"]: asset for asset in catalog}
    tag_list = []
    for public_id in selected_ids:
        asset = by_id.get(public_id)
        if asset:
            tag_list.extend(clean_tags(asset.get("tags")))
    return most_frequent(tag_list, top_n)


def recommend(selected_ids, catalog, top_n=TOP_TAGS, limit=None):
    """Rank catalog assets that share the selection's most frequent tags.

    An asset qualifies if it has at least one of the top tags and wasn't
    selected. Assets are ordered by score (sum of the matched tags' frequency
    in the selection), then by catalog order so results are stable.
    """
    profile = dict(build_profile(selected_ids, catalog, top_n))
    if not profile:
        return []

    selected = set(selected_ids)
    scored = []
    for position, asset in enumerate(catalog):
        if asset["public_id"] in selected:
            continue
        matched = [tag for tag in clean_tags(asset.get("tags")) if tag in profile]
        if matched:
            score = sum(profile[tag] for tag in matched)
            scored.append((-score, position, asset, matched))

    scored.sort(key=lambda item: (item[0], item[1]))
    results = [
        dict(asset, matched_tags=matched, score=-neg_score)
        for neg_score, _, asset, matched in scored
    ]
    return results[:limit] if limit else results
