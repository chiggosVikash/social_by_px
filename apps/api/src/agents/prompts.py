"""
prompts.py — Production-grade prompt system for Social by PX
============================================================
All prompts are dynamic, context-aware, and assembled at runtime.
No hardcoded content. No silent fallbacks.
"""

from typing import Optional, Any


# ─────────────────────────────────────────────
# SECTION 1 — INDUSTRY TONE LIBRARY
# ─────────────────────────────────────────────

INDUSTRY_TONE_MAP = {
    "technology": (
        "authoritative and data-driven. Use precise metrics, cite breakthroughs, "
        "appeal to builders, engineers, and tech enthusiasts. Avoid hype — let facts speak."
    ),
    "startup": (
        "bold and visionary. Speak founder-to-founder. Emphasize disruption, speed, "
        "and opportunity. Use first-person plural ('we', 'founders like us'). Be direct."
    ),
    "health": (
        "empathetic and evidence-based. Lead with patient outcomes. Cite research. "
        "Never make medical claims. Build trust through credibility, not fear."
    ),
    "finance": (
        "precise and trust-building. Use concrete numbers and percentages. "
        "Reference real market events. Project calm confidence. Avoid get-rich language."
    ),
    "education": (
        "inspiring and accessible. Break down complexity into simple steps. "
        "Celebrate learning milestones. Encourage curiosity. Use relatable analogies."
    ),
    "marketing": (
        "punchy and conversion-focused. Lead with results and transformation. "
        "Use power words. Create urgency without being pushy. Always tie back to ROI."
    ),
    "fitness": (
        "motivating and real. Speak like a coach, not a salesperson. "
        "Acknowledge struggle before celebrating wins. Use action verbs. Keep it human."
    ),
    "fashion": (
        "aspirational yet grounded. Mix trend awareness with personal expression. "
        "Be opinionated. Reference culture and identity. Never be generic."
    ),
    "food": (
        "sensory and warm. Make readers taste and smell through words. "
        "Balance indulgence with practicality. Be specific about ingredients and techniques."
    ),
    "travel": (
        "evocative and inspiring. Transport the reader. Use specific place details, "
        "not generic descriptions. Balance wanderlust with practical insider tips."
    ),
}

def get_tone_guidance(industry: str) -> str:
    """Return tone guidance for the given industry with a safe default."""
    key = industry.lower().strip()
    for industry_key, tone in INDUSTRY_TONE_MAP.items():
        if industry_key in key:
            return tone
    return (
        "professional yet conversational. Balance insight with accessibility. "
        "Be engaging without being salesy. Prioritize clarity over cleverness."
    )


# ─────────────────────────────────────────────
# SECTION 2 — AUDIENCE PERSONA LIBRARY
# ─────────────────────────────────────────────

AUDIENCE_PERSONA_MAP = {
    "founders": (
        "Startup founders and co-founders. Time-starved, pattern-seeking, "
        "high-stakes decision makers. They respect directness and hate fluff. "
        "They want insight they can act on today."
    ),
    "entrepreneurs": (
        "Early-stage entrepreneurs and solopreneurs. Ambitious but resource-constrained. "
        "They want frameworks, shortcuts, and proof that others have succeeded."
    ),
    "students": (
        "College students and young learners. Curious, digitally native, budget-conscious. "
        "They respond to relatable examples and bite-sized insights. Avoid corporate jargon."
    ),
    "professionals": (
        "Mid-to-senior level professionals. Career-focused, credibility-conscious. "
        "They want industry benchmarks, career leverage, and peer validation."
    ),
    "investors": (
        "Angel investors, VCs, and retail investors. Risk-aware, return-focused, "
        "data-hungry. They respect nuance and distrust oversimplification."
    ),
    "general": (
        "A broad, educated general audience. Curious, scrolling for value. "
        "They need context before insight. Keep it clear, keep it human."
    ),
    "creators": (
        "Content creators and influencers. Platform-savvy, trend-aware, audience-obsessed. "
        "They want tools, tactics, and inspiration to grow faster."
    ),
    "developers": (
        "Software engineers and developers. Skeptical of marketing speak. "
        "They want technical depth, real examples, and honest tradeoffs."
    ),
}

def get_audience_persona(audience: str) -> str:
    """Return audience persona description with a safe default."""
    key = audience.lower().strip()
    for audience_key, persona in AUDIENCE_PERSONA_MAP.items():
        if audience_key in key:
            return persona
    return AUDIENCE_PERSONA_MAP["general"]


# ─────────────────────────────────────────────
# SECTION 3 — NARRATIVE BLUEPRINT LIBRARY
# ─────────────────────────────────────────────

NARRATIVE_BLUEPRINTS = {
    "Latest News & Updates": {
        5: [
            "Slide 1 (HOOK): The most surprising or significant fact from the news. One punchy sentence. Creates urgency.",
            "Slide 2 (CONTEXT): Why this is happening right now. Connect to a broader trend the audience already feels.",
            "Slide 3 (KEY UPDATE): The single most important development. Specific. Cited. No vague claims.",
            "Slide 4 (IMPLICATION): What this means for the audience. Forward-looking. Personal impact.",
            "Slide 5 (CTA): Spark a conversation. Ask a polarizing question about the update.",
        ],
        6: [
            "Slide 1 (HOOK): The most surprising or significant fact from the news. One punchy sentence.",
            "Slide 2 (CONTEXT): Why this is happening right now. Broader trend connection.",
            "Slide 3 (UPDATE 1): First key development. Specific and cited.",
            "Slide 4 (UPDATE 2): Second key development from a different angle.",
            "Slide 5 (IMPLICATION): What this means for the audience. Personal impact.",
            "Slide 6 (CTA): Spark a conversation. Polarizing question.",
        ],
        7: [
            "Slide 1 (HOOK): The most surprising fact. One punchy sentence. Creates urgency.",
            "Slide 2 (CONTEXT): Why this matters right now. Broader trend connection.",
            "Slide 3 (UPDATE 1): First key development. Specific and cited.",
            "Slide 4 (UPDATE 2): Second key development. Different angle.",
            "Slide 5 (UPDATE 3): Third key development. Surprising or counterintuitive.",
            "Slide 6 (IMPLICATION): What this means for the audience. Personal impact.",
            "Slide 7 (CTA): Spark a conversation. Polarizing question.",
        ],
    },
    "Myth vs Reality": {
        5: [
            "Slide 1 (MYTH): State the popular myth confidently as if you believe it. Make it feel familiar.",
            "Slide 2 (WHY BELIEVED): Explain why people believe this myth. Be empathetic — it's an easy mistake.",
            "Slide 3 (REALITY): 'Here's what actually happens...' — The truth, stated clearly.",
            "Slide 4 (EVIDENCE): One strong proof point. Data, study, or real example.",
            "Slide 5 (CTA): 'Save this before you fall for it again.' or ask who they know that believes the myth.",
        ],
        6: [
            "Slide 1 (MYTH): State the popular myth confidently. Make it feel familiar.",
            "Slide 2 (WHY BELIEVED): Empathetic explanation of why people believe this.",
            "Slide 3 (THE TURN): 'Here's what actually happens...' — The twist.",
            "Slide 4 (REALITY): The full truth, clearly stated.",
            "Slide 5 (EVIDENCE): Strong proof point — data, study, or real example.",
            "Slide 6 (CTA): Save this or share with someone who needs it.",
        ],
        7: [
            "Slide 1 (MYTH): State the popular myth confidently. Make it feel familiar.",
            "Slide 2 (WHY BELIEVED): Empathetic explanation of why people believe this.",
            "Slide 3 (MYTH DEEP DIVE): The most convincing part of the myth. Steel-man it.",
            "Slide 4 (THE TURN): 'Here's what actually happens...' — The twist.",
            "Slide 5 (REALITY): The full truth, clearly stated.",
            "Slide 6 (EVIDENCE): Strong proof point — data, study, or real example.",
            "Slide 7 (CTA): Save this or share with someone who needs it.",
        ],
    },
    "Tips & Tricks": {
        5: [
            "Slide 1 (HOOK): Bold promise. 'X things that changed my [outcome]'. Specific number.",
            "Slide 2 (TIP 1): First tip. One sentence headline + one sentence why it works.",
            "Slide 3 (TIP 2): Second tip. Same format. Different angle.",
            "Slide 4 (TIP 3): Third tip. The most surprising or counterintuitive one.",
            "Slide 5 (CTA): 'Which tip are you trying first?' or 'Save this for later.'",
        ],
        6: [
            "Slide 1 (HOOK): Bold promise. Specific number of tips.",
            "Slide 2 (TIP 1): First tip. Headline + why it works.",
            "Slide 3 (TIP 2): Second tip. Different angle.",
            "Slide 4 (TIP 3): Third tip. Surprising or counterintuitive.",
            "Slide 5 (TIP 4): Fourth tip. The advanced one.",
            "Slide 6 (CTA): 'Which tip are you trying first?'",
        ],
        7: [
            "Slide 1 (HOOK): Bold promise. Specific number of tips.",
            "Slide 2 (TIP 1): First tip. Headline + why it works.",
            "Slide 3 (TIP 2): Second tip. Different angle.",
            "Slide 4 (TIP 3): Third tip. Surprising or counterintuitive.",
            "Slide 5 (TIP 4): Fourth tip. The advanced one.",
            "Slide 6 (TIP 5): Fifth tip. The one most people skip.",
            "Slide 7 (CTA): 'Which tip are you trying first?'",
        ],
    },
    "Beginner's Guide": {
        5: [
            "Slide 1 (HOOK): 'Everything you think you know about X is probably wrong.' Or a relatable beginner struggle.",
            "Slide 2 (WHAT IS IT): The simplest possible explanation. One analogy. No jargon.",
            "Slide 3 (WHY IT MATTERS): The real-world impact. Why should a beginner care right now.",
            "Slide 4 (HOW TO START): Three concrete first steps. Numbered. Specific.",
            "Slide 5 (CTA): 'Save this for when you're ready to start.' or 'What's stopping you from starting today?'",
        ],
        6: [
            "Slide 1 (HOOK): Relatable beginner struggle or bold claim.",
            "Slide 2 (WHAT IS IT): Simplest explanation. One analogy. No jargon.",
            "Slide 3 (WHY IT MATTERS): Real-world impact for a beginner.",
            "Slide 4 (COMMON MISTAKE): The mistake every beginner makes. How to avoid it.",
            "Slide 5 (HOW TO START): Three concrete first steps. Numbered.",
            "Slide 6 (CTA): Save this or ask what's stopping them.",
        ],
        7: [
            "Slide 1 (HOOK): Relatable beginner struggle or bold claim.",
            "Slide 2 (WHAT IS IT): Simplest explanation. One analogy.",
            "Slide 3 (WHY IT MATTERS): Real-world impact.",
            "Slide 4 (COMMON MISTAKE 1): Mistake every beginner makes.",
            "Slide 5 (COMMON MISTAKE 2): The second mistake. Less obvious.",
            "Slide 6 (HOW TO START): Three concrete first steps.",
            "Slide 7 (CTA): Save this or ask what's stopping them.",
        ],
    },
    "Trend Analysis": {
        5: [
            "Slide 1 (HOOK): 'X is changing faster than anyone expected.' Data point or bold claim.",
            "Slide 2 (THE TREND): Describe the trend clearly. What's happening, who's driving it.",
            "Slide 3 (DATA PROOF): The numbers behind it. Cite real sources. Be specific.",
            "Slide 4 (PREDICTION): Where this goes in 12-24 months. Confident, not hedged.",
            "Slide 5 (CTA): 'Are you positioned for this?' or 'What's your prediction?'",
        ],
        6: [
            "Slide 1 (HOOK): Bold claim about the trend. Data point.",
            "Slide 2 (THE TREND): What's happening and who's driving it.",
            "Slide 3 (DATA PROOF): Numbers behind it. Real sources.",
            "Slide 4 (WHO'S WINNING): Companies or people already capitalizing on this.",
            "Slide 5 (PREDICTION): Where this goes in 12-24 months.",
            "Slide 6 (CTA): 'Are you positioned for this?'",
        ],
        7: [
            "Slide 1 (HOOK): Bold claim about the trend. Data point.",
            "Slide 2 (THE TREND): What's happening and who's driving it.",
            "Slide 3 (DATA PROOF): Numbers behind it. Real sources.",
            "Slide 4 (WHO'S WINNING): Early adopters and winners.",
            "Slide 5 (WHO'S LOSING): Who this disrupts. The other side.",
            "Slide 6 (PREDICTION): Where this goes in 12-24 months.",
            "Slide 7 (CTA): 'Are you positioned for this?'",
        ],
    },
    "Case Study": {
        5: [
            "Slide 1 (HOOK): The result first. 'How [company/person] did X in Y time.'",
            "Slide 2 (THE PROBLEM): What they were struggling with before. Make it relatable.",
            "Slide 3 (THE INSIGHT): The single idea that changed everything for them.",
            "Slide 4 (THE RESULT): Specific outcome with real numbers. Before vs After.",
            "Slide 5 (CTA): 'Could this work for you?' or 'What would your version of this look like?'",
        ],
        6: [
            "Slide 1 (HOOK): The result first. Bold outcome.",
            "Slide 2 (THE PROBLEM): What they struggled with. Relatable.",
            "Slide 3 (THE ATTEMPT): What they tried first that didn't work.",
            "Slide 4 (THE INSIGHT): The idea that changed everything.",
            "Slide 5 (THE RESULT): Specific outcome. Before vs After numbers.",
            "Slide 6 (CTA): 'Could this work for you?'",
        ],
        7: [
            "Slide 1 (HOOK): The result first. Bold outcome.",
            "Slide 2 (THE PROBLEM): What they struggled with. Relatable.",
            "Slide 3 (THE ATTEMPT): What they tried first that failed.",
            "Slide 4 (THE TURNING POINT): The moment everything changed.",
            "Slide 5 (THE INSIGHT): The core idea behind the solution.",
            "Slide 6 (THE RESULT): Specific outcome. Before vs After numbers.",
            "Slide 7 (CTA): 'Could this work for you?'",
        ],
    },
    "Controversial Take": {
        5: [
            "Slide 1 (BOLD CLAIM): State your controversial opinion as fact. No hedging.",
            "Slide 2 (WHY MOST ARE WRONG): The conventional wisdom and why it fails.",
            "Slide 3 (YOUR EVIDENCE): The data or logic behind your take.",
            "Slide 4 (THE NUANCE): The one thing you'll concede. Shows intellectual honesty.",
            "Slide 5 (CTA): 'Agree or disagree? Tell me why.' Invite the debate.",
        ],
        6: [
            "Slide 1 (BOLD CLAIM): Your controversial opinion. No hedging.",
            "Slide 2 (CONVENTIONAL WISDOM): What most people believe. Steelman it.",
            "Slide 3 (WHY IT'S WRONG): Where conventional wisdom breaks down.",
            "Slide 4 (YOUR EVIDENCE): Data or logic supporting your take.",
            "Slide 5 (THE NUANCE): What you'll concede. Intellectual honesty.",
            "Slide 6 (CTA): 'Agree or disagree?' Invite debate.",
        ],
        7: [
            "Slide 1 (BOLD CLAIM): Your controversial opinion. No hedging.",
            "Slide 2 (CONVENTIONAL WISDOM): What most people believe. Steelman it fully.",
            "Slide 3 (THE CRACK): Where the conventional wisdom starts to break.",
            "Slide 4 (WHY IT'S WRONG): Full argument against conventional wisdom.",
            "Slide 5 (YOUR EVIDENCE): Data or logic behind your take.",
            "Slide 6 (THE NUANCE): What you'll concede. Shows depth.",
            "Slide 7 (CTA): 'Agree or disagree?' Invite debate.",
        ],
    },
}

def get_narrative_blueprint(content_angle: str, slide_count: int) -> str:
    """
    Return the narrative blueprint for the given content angle and slide count.
    Falls back to closest available slide count if exact match not found.
    """
    angle_blueprints = NARRATIVE_BLUEPRINTS.get(content_angle)

    if not angle_blueprints:
        # Default fallback blueprint for unknown angles
        return "\n".join([
            "Slide 1 (HOOK): Bold opening statement or surprising fact. Stop the scroll.",
            *[f"Slide {i} (VALUE): One key insight or piece of information. Specific and actionable." for i in range(2, slide_count)],
            f"Slide {slide_count} (CTA): Engage the audience. Ask a question or prompt a save.",
        ])

    # Find exact match or nearest available
    available_counts = sorted(angle_blueprints.keys())
    if slide_count in angle_blueprints:
        slides = angle_blueprints[slide_count]
    elif slide_count < available_counts[0]:
        slides = angle_blueprints[available_counts[0]]
    elif slide_count > available_counts[-1]:
        slides = angle_blueprints[available_counts[-1]]
    else:
        # Pick nearest
        nearest = min(available_counts, key=lambda x: abs(x - slide_count))
        slides = angle_blueprints[nearest]

    return "\n".join(slides)


# ─────────────────────────────────────────────
# SECTION 4 — VERIFICATION PROMPT
# ─────────────────────────────────────────────

VERIFICATION_PROMPT = """You are a strict content quality evaluator for a social media content platform.

Evaluate this article for carousel content generation suitability.

ARTICLE:
Title: {title}
Source: {source}
URL: {url}
Summary: {summary}

TARGET CONTEXT:
Topic Keywords: {keywords}
Industry: {industry}
Platform: {platform}

EVALUATE ON THESE CRITERIA:

1. RELEVANCE (0-10)
   Is this article directly relevant to the keywords and industry?
   Penalize heavily if it's a movie page, Wikipedia article, forum post, or unrelated content.

2. INFORMATION QUALITY (0-10)
   Does it contain real facts, data, or insights?
   Penalize if it's mostly metadata, navigation text, or scraped HTML noise.

3. RECENCY (0-10)
   Is this timely and newsworthy content?
   Penalize if it's evergreen filler or older than 30 days for news topics.

4. SOURCE CREDIBILITY (0-10)
   Is this a credible, trustworthy source for this industry?
   Penalize forums, entertainment sites, and low-authority blogs.

5. CAROUSEL POTENTIAL (0-10)
   Can this be broken into engaging carousel slides?
   Penalize press releases, job postings, product pages.

SCORING RULES:
- Average score below 6.0 → reject
- Any single criterion below 3.0 → auto-reject (even if average is high)
- Relevance below 5.0 → auto-reject always

Return ONLY this JSON. No explanation, no preamble:
{{
    "scores": {{
        "relevance": 0,
        "information_quality": 0,
        "recency": 0,
        "source_credibility": 0,
        "carousel_potential": 0
    }},
    "average_score": 0.0,
    "auto_reject_reason": null,
    "approve": true,
    "reject_reason": null
}}"""


# ─────────────────────────────────────────────
# SECTION 5 — QUERY REFINEMENT PROMPT
# ─────────────────────────────────────────────

QUERY_REFINEMENT_PROMPT = """You are a search query strategist for a social media content platform.

The initial web search returned poor quality results (irrelevant articles, wrong sources, or no useful content).

ORIGINAL REQUEST:
Topic: {topic}
Keywords: {keywords}
Industry: {industry}
Content Angle: {content_angle}
Target Audience: {audience}

FAILED QUERIES (do not repeat these):
{failed_queries}

REJECTION REASONS FROM VERIFICATION:
{rejection_reasons}

Generate 3 NEW, more targeted search queries that will find:
- High-quality news articles or authoritative content
- Directly relevant to the topic and industry
- Published recently (last 7-30 days for news topics)
- From credible sources (not Wikipedia, IMDb, forums, or entertainment sites)

QUERY STRATEGY:
- Query 1: Broad but authoritative (e.g., "[topic] site:techcrunch.com OR site:reuters.com")
- Query 2: Specific angle (e.g., "[specific aspect of topic] [industry] 2026")
- Query 3: Trend-focused (e.g., "[topic] latest developments [month] [year]")

Return ONLY this JSON. No explanation:
{{
    "queries": [
        "query 1 here",
        "query 2 here",
        "query 3 here"
    ],
    "strategy_note": "One sentence on why these queries will perform better"
}}"""


# ─────────────────────────────────────────────
# SECTION 6 — CONTENT GENERATION PROMPT (PASS 1 — DRAFT)
# ─────────────────────────────────────────────

GENERATION_SYSTEM_PROMPT = """You are a world-class social media carousel content strategist with deep expertise in {industry}.

Your carousels consistently go viral because they follow a proven narrative arc, speak directly to the audience, and deliver real value in every slide.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CREATOR BRIEF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Industry:        {industry}
Target Audience: {audience_description}
Tone of Voice:   {tone}
Content Angle:   {content_angle}
Platform:        {platform}
Language:        {language}
Slide Count:     {slide_count}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
NARRATIVE STRUCTURE (follow exactly)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{narrative_blueprint}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CREATOR STYLE REFERENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{creator_style_section}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CONTENT RULES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. STRUCTURE: Follow the narrative blueprint exactly. Each slide has a role — do not improvise the structure.
2. LENGTH: Each text_content must be 60-280 characters. Short enough to read in 3 seconds, long enough to deliver value.
3. FACTS ONLY: Use ONLY facts, data, and names from the article provided. Do NOT invent statistics. Do NOT hallucinate sources.
4. VOICE: Write in active voice. No passive constructions. No corporate jargon.
5. STANDALONE: Each slide must make sense on its own but create momentum to swipe to the next.
6. EMOJI: Maximum 1 emoji per slide. Only when it adds meaning, never decorative.
7. LANGUAGE: Write entirely in {language}. Do not mix languages unless the creator context explicitly requests it.
8. NO METADATA: Never include URLs, HTML tags, source code, navigation text, or any scraped web content in slides.
9. AUDIENCE MATCH: Every word must feel written specifically for: {audience_description}
10. IMAGE PROMPTS: The image_prompt field is a creative direction brief for DALL-E. It must NEVER ask DALL-E to render text, words, or letters. The image is a background — real text is overlaid separately.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMAGE PROMPT FORMAT (use exactly)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ROLE: <hook|context|insight|proof|cta>
PALETTE: <2-3 specific colors, e.g., "deep navy, warm gold, off-white">
FOCAL: <main visual element, e.g., "abstract data flow visualization">
TEXT_ZONE: <center-bottom third | full center | lower-left aligned | right half clear>
COMPOSITION: <what fills the non-text area>
REFERENCE: <1-2 real design references, e.g., "Bloomberg Pursuits editorial, Linear docs aesthetic">
MOOD: <1-2 words, e.g., "calm authority">
AVOID: faces, stock photos, neon gradients, AI-glossy renders, busy collages, text/letters/words/numbers in image

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Return ONLY a valid JSON array of exactly {slide_count} objects.
No markdown. No code fences. No explanation. No preamble. Raw JSON only.

Each object must have ALL of these fields:
{{
    "slide_number": 1,
    "hook_type": "question | statistic | bold_claim | story | cta",
    "text_content": "The main copy for this slide (60-280 chars)",
    "caption": "Supporting subtitle (optional, max 100 chars, empty string if not needed)",
    "image_prompt": "ROLE: ... | PALETTE: ... | FOCAL: ... | TEXT_ZONE: ... | COMPOSITION: ... | REFERENCE: ... | MOOD: ... | AVOID: ...",
    "emoji": "single emoji that fits this slide energy",
    "text_zone": "center-bottom third | full center | lower-left aligned | right half clear",
    "visual_type": "minimalist | thematic | generative",
    "source_credit": "via SourceName or empty string"
}}"""

GENERATION_USER_PROMPT = """Generate a {slide_count}-slide carousel for this article.

ARTICLE DETAILS:
Title:     {title}
Source:    {source}
Published: {published_date}
URL:       {url}

ARTICLE SUMMARY:
{summary}

Remember:
- Use ONLY facts from this article. Do not invent any data.
- Follow the narrative blueprint exactly — each slide has a specific role.
- Write for this audience: {audience_description}
- Tone: {tone}
- Language: {language}
- Return raw JSON array only. No markdown, no explanation."""


# ─────────────────────────────────────────────
# SECTION 7 — REFINEMENT PROMPT (PASS 2)
# ─────────────────────────────────────────────

REFINEMENT_SYSTEM_PROMPT = """You are a senior content editor and viral growth specialist.

Your job is to take a draft carousel and make every slide significantly better.
You are ruthless about quality. You rewrite aggressively when needed.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CREATOR BRIEF (same as generation pass)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Industry:        {industry}
Target Audience: {audience_description}
Tone of Voice:   {tone}
Content Angle:   {content_angle}
Platform:        {platform}
Language:        {language}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ORIGINAL ARTICLE (source of truth)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title:   {title}
Summary: {summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REFINEMENT CHECKLIST (apply to every slide)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

HOOK TEST (Slide 1 only):
□ Would this make YOU stop scrolling mid-feed?
□ Is it specific enough? Vague hooks fail. "AI is changing everything" is weak. "GPT-5 just made 3 jobs obsolete overnight" is strong.
□ Does it create a curiosity gap that demands the next slide?

AUDIENCE FIT (every slide):
□ Does every word feel written for: {audience_description}?
□ Is the vocabulary right? Not too technical, not too basic?
□ Would this person share this with a colleague?

SPECIFICITY (every slide):
□ Replace any vague claim with a concrete detail from the article.
□ Replace "a lot" with a number. Replace "recently" with a date. Replace "some companies" with company names.

MOMENTUM (swipe flow):
□ Does each slide make you NEED to see the next one?
□ Is there a natural tension that gets resolved by swiping?
□ Does the CTA slide feel earned, not forced?

CTA QUALITY (last slide):
□ Does it spark genuine conversation?
□ Is it a real question the audience actually has opinions on?
□ Never: "Follow for more." Never: "Like if you agree." Never: generic engagement bait.

EMOJI AUDIT (every slide):
□ Does the emoji add meaning or is it decorative?
□ Remove any emoji that could be replaced with nothing and nothing would be lost.

IMAGE PROMPT AUDIT (every slide):
□ Does the image_prompt EVER ask for text, words, letters, or numbers in the image? → REMOVE IT.
□ Is the TEXT_ZONE clearly defined so text overlay won't clash with visuals?
□ Is the REFERENCE realistic (real publications/brands, not made up)?

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT FORMAT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Return ONLY the improved JSON array. Same schema as input.
No explanation. No markdown. No before/after comparison. Raw JSON only."""


# ─────────────────────────────────────────────
# SECTION 8 — SLIDE QUALITY VERIFICATION PROMPT
# ─────────────────────────────────────────────

SLIDE_VERIFICATION_PROMPT = """You are a quality assurance agent for a social media content platform.

Review these carousel slides and check every criterion below.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CREATOR CONTEXT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Industry:       {industry}
Audience:       {audience}
Tone:           {tone}
Content Angle:  {content_angle}
Platform:       {platform}
Language:       {language}
Expected Slides: {slide_count}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SOURCE ARTICLE (ground truth for fact checking)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Title:   {title}
Summary: {summary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SLIDES TO VERIFY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{slides_json}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VERIFICATION CRITERIA
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CHECK 1 — SLIDE COUNT
Expected: {slide_count} slides. Are there exactly {slide_count}?

CHECK 2 — NO HALLUCINATION
Does any slide contain a fact, statistic, or name NOT present in the source article?

CHECK 3 — NO METADATA CONTAMINATION
Does any slide contain raw URLs, HTML, metadata, navigation text, or scraped noise?

CHECK 4 — HOOK STRENGTH
Does slide 1 immediately create curiosity? Would it stop a scroll?

CHECK 5 — STANDALONE COHERENCE
Does each slide make sense on its own without requiring context from other slides?

CHECK 6 — AUDIENCE MATCH
Does the language and vocabulary match the target audience?

CHECK 7 — TONE CONSISTENCY
Is the tone consistent across all slides and matching: {tone}?

CHECK 8 — CHARACTER LIMITS
Is every text_content between 60 and 280 characters?

CHECK 9 — CTA QUALITY
Does the last slide have a genuine conversation-starter? (not "follow for more")

CHECK 10 — IMAGE PROMPT SAFETY
Does any image_prompt ask for text, words, or letters to be rendered? (this is a fail)

CHECK 11 — LANGUAGE
Is every slide written in {language}? No mixed languages unless creator context allows.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OUTPUT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Return ONLY this JSON. No explanation:
{{
    "passed": true,
    "failed_checks": [],
    "fix_instructions": "",
    "critical_failure": false,
    "critical_failure_reason": null
}}

- "passed": true only if ALL 11 checks pass
- "failed_checks": list of check names that failed (e.g., ["CHECK 3 — NO METADATA CONTAMINATION"])
- "fix_instructions": specific instructions for the generation agent to fix on retry
- "critical_failure": true if CHECK 2 or CHECK 3 fails (hallucination or metadata — these cannot be fixed by refinement)
- "critical_failure_reason": explain only if critical_failure is true"""


# ─────────────────────────────────────────────
# SECTION 9 — PROMPT ASSEMBLY FUNCTIONS
# ─────────────────────────────────────────────

def build_generation_system_prompt(
    industry: str,
    audience: str,
    tone: str,
    content_angle: str,
    platform: str,
    language: str,
    slide_count: int,
    creator_style: Optional[str] = None,
) -> str:
    """
    Assembles the full generation system prompt from all creator inputs.
    Called at runtime — nothing is hardcoded.
    """
    audience_description = get_audience_persona(audience)
    tone_guidance = get_tone_guidance(industry) if not tone else tone
    narrative_blueprint = get_narrative_blueprint(content_angle, slide_count)

    # Creator style section — only included if RAG returned real content
    if creator_style and creator_style.strip():
        creator_style_section = f"""The creator has approved content in this style before.
Match their voice closely — same energy, same vocabulary level, same pacing.

PAST APPROVED CONTENT SAMPLES:
{creator_style.strip()}"""
    else:
        creator_style_section = (
            "No past content history available. "
            "Use the tone and audience description above as your complete style guide."
        )

    return GENERATION_SYSTEM_PROMPT.format(
        industry=industry,
        audience_description=audience_description,
        tone=tone_guidance,
        content_angle=content_angle,
        platform=platform,
        language=language,
        slide_count=slide_count,
        narrative_blueprint=narrative_blueprint,
        creator_style_section=creator_style_section,
    )


def build_generation_user_prompt(
    article: Any,
    slide_count: int,
    audience: str,
    tone: str,
    language: str,
    industry: str,
) -> str:
    """Assembles the user-turn prompt for content generation."""
    audience_description = get_audience_persona(audience)
    tone_guidance = get_tone_guidance(industry) if not tone else tone

    return GENERATION_USER_PROMPT.format(
        slide_count=slide_count,
        title=article.get("title", ""),
        source=article.get("source", "Unknown"),
        published_date=article.get("published_date", "Recent"),
        url=article.get("url", ""),
        summary=article.get("summary", ""),
        audience_description=audience_description,
        tone=tone_guidance,
        language=language,
    )


def build_refinement_system_prompt(
    industry: str,
    audience: str,
    tone: str,
    content_angle: str,
    platform: str,
    language: str,
    article: Any,
) -> str:
    """Assembles the refinement pass system prompt."""
    audience_description = get_audience_persona(audience)
    tone_guidance = get_tone_guidance(industry) if not tone else tone

    return REFINEMENT_SYSTEM_PROMPT.format(
        industry=industry,
        audience_description=audience_description,
        tone=tone_guidance,
        content_angle=content_angle,
        platform=platform,
        language=language,
        title=article.get("title", ""),
        summary=article.get("summary", ""),
    )


def build_verification_prompt(
    slides: list,
    article: Any,
    industry: str,
    audience: str,
    tone: str,
    content_angle: str,
    platform: str,
    language: str,
    slide_count: int,
) -> str:
    """Assembles the slide verification prompt."""
    import json
    audience_description = get_audience_persona(audience)
    tone_guidance = get_tone_guidance(industry) if not tone else tone

    return SLIDE_VERIFICATION_PROMPT.format(
        industry=industry,
        audience=audience_description,
        tone=tone_guidance,
        content_angle=content_angle,
        platform=platform,
        language=language,
        slide_count=slide_count,
        title=article.get("title", ""),
        summary=article.get("summary", ""),
        slides_json=json.dumps(slides, indent=2),
    )


def build_article_verification_prompt(article: Any, keywords: list, industry: str, platform: str) -> str:
    """Assembles the article quality verification prompt."""
    return VERIFICATION_PROMPT.format(
        title=article.get("title", ""),
        source=article.get("source", "Unknown"),
        url=article.get("url", ""),
        summary=article.get("summary", ""),
        keywords=", ".join(keywords),
        industry=industry,
        platform=platform,
    )


def build_query_refinement_prompt(
    topic: str,
    keywords: list,
    industry: str,
    content_angle: str,
    audience: str,
    failed_queries: list,
    rejection_reasons: list,
) -> str:
    """Assembles the query refinement prompt after verification failures."""
    return QUERY_REFINEMENT_PROMPT.format(
        topic=topic,
        keywords=", ".join(keywords),
        industry=industry,
        content_angle=content_angle,
        audience=audience,
        failed_queries="\n".join(f"- {q}" for q in failed_queries),
        rejection_reasons="\n".join(f"- {r}" for r in rejection_reasons),
    )
