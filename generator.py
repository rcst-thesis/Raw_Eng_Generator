"""
generator.py — Core sentence generation engine  (v3 — massively expanded)

28 domains · 22 generation strategies · 3 difficulty tiers
600 + dialogue pairs · 900 + standalone sentences
Paraphrase map of 80 + word swaps · Rolling MD5 deduplication cache
New strategies: rhetorical_question, aphorism, anecdote_opener, list_sentence,
                hypothetical, reported_speech, causal_chain, contrast_pair,
                imperative, reflection, analogy, proverb_twist, future_tense,
                enumeration, sensory, quote_attribution, definition, news_headline

Output schema per row:  id,english_text
"""

from __future__ import annotations

import hashlib
import logging
import random
from dataclasses import dataclass
from typing import Generator, Optional

logger = logging.getLogger(__name__)

# ════════════════════════════════════════════════════════════════════════════
# SHARED LINGUISTIC BANKS  (greatly expanded)
# ════════════════════════════════════════════════════════════════════════════

CONJUNCTIONS = [
    "and", "but", "so", "yet", "because", "although", "while",
    "since", "unless", "whenever", "even though", "as long as",
    "whereas", "given that", "provided that", "in case", "now that",
    "as soon as", "even if", "rather than", "not only that but",
    "besides", "furthermore", "consequently", "therefore", "nonetheless",
    "meanwhile", "in addition", "on top of that", "by contrast",
    "in spite of this", "nevertheless", "all the same", "that said",
]

TRANSITIONS = [
    "However,", "Meanwhile,", "As a result,", "In addition,",
    "On the other hand,", "For example,", "That said,", "Furthermore,",
    "Consequently,", "Nevertheless,", "In contrast,", "At the same time,",
    "Above all,", "To clarify,", "In other words,", "To put it simply,",
    "Surprisingly,", "Notably,", "What is more,", "To illustrate,",
    "By the same token,", "In light of this,", "As a matter of fact,",
    "All things considered,", "On balance,", "With that in mind,",
    "Broadly speaking,", "More importantly,", "Quite remarkably,",
    "To summarise,", "In turn,", "For this reason,", "At first glance,",
    "Looking at this differently,", "Taken together,", "Beyond that,",
    "As a consequence,", "Interestingly enough,", "To be precise,",
    "Building on that,", "Stepping back,", "In practical terms,",
    "Without question,", "In a similar vein,", "To add to this,",
    "Put simply,", "It follows that,", "Bearing this in mind,",
    "Equally important,", "Just as significantly,", "On a related note,",
]

TIME_PHRASES = [
    "Yesterday,", "Last week,", "Every morning,", "Once in a while,",
    "Lately,", "Earlier today,", "On most days,", "From time to time,",
    "Recently,", "Just a moment ago,", "Not long ago,", "Over the weekend,",
    "This afternoon,", "Early in the morning,", "At the end of the day,",
    "Just last month,", "For the past few weeks,", "Every now and then,",
    "First thing in the morning,", "Late last night,", "By the end of the week,",
    "During the holidays,", "A few days ago,", "Throughout the year,",
    "Every single day,", "Since last Tuesday,", "On a regular basis,",
    "In the evenings,", "Several months ago,", "Just this morning,",
    "Over the past decade,", "Only yesterday,", "Not so long ago,",
    "On a quiet Sunday,", "In the middle of the night,", "Once a month,",
    "Twice a week,", "Just before the weekend,", "By the time spring arrived,",
    "Throughout last semester,", "Back in those days,", "As the weeks passed,",
    "Long before sunrise,", "Towards the end of the month,",
    "At the start of the new year,", "During rush hour,",
    "On a cold winter's morning,", "Right before the deadline,",
]

FILLER_OPENERS = [
    "Did you know that", "I think", "It seems like", "Apparently,",
    "Most people agree that", "Studies suggest that", "Experts say that",
    "It is worth noting that", "Interestingly,", "As far as I know,",
    "To be honest,", "Believe it or not,", "From what I understand,",
    "It turns out that", "Some people say that", "A lot of people feel that",
    "It is generally accepted that", "You might not realise that",
    "What many people forget is that", "More often than not,",
    "One thing that stands out is that", "It is quite clear that",
    "Research has shown that", "Something worth mentioning is that",
    "You would be surprised to learn that", "It goes without saying that",
    "The good news is that", "Something I have noticed is that",
    "The truth is that", "What is often overlooked is that",
    "Contrary to what many assume,", "The evidence suggests that",
    "What is particularly striking is that", "It is no secret that",
    "Many would argue that", "Looking at the evidence,",
    "From a practical standpoint,", "The reality is that",
    "It may come as a surprise that", "One rarely discussed fact is that",
    "Not many people realise that", "It bears repeating that",
]

CONDITION_OPENERS = [
    "If you ask me,", "If that is the case,", "Should you need help,",
    "Assuming everything goes to plan,", "Once you get used to it,",
    "Given the right conditions,", "When the time is right,",
    "Provided you follow the steps,", "In the event that something goes wrong,",
    "As long as you stay consistent,", "Whenever you feel ready,",
    "If everything works as expected,", "Once the process is complete,",
    "Unless something changes,", "Whether or not you agree,",
    "Should the opportunity arise,", "If handled correctly,",
    "Given enough time and patience,", "Were you to try this approach,",
    "On the condition that all parties cooperate,",
    "Supposing the plan goes ahead,", "Provided the data holds,",
    "If the trend continues,", "Once the initial hurdle is cleared,",
    "Should the circumstances allow,", "In a best-case scenario,",
]

COMPARISON_STARTERS = [
    "Compared to last year,", "Unlike what most people expect,",
    "In comparison to the old method,", "Much like the previous version,",
    "Similar to what we saw before,", "In the same way,",
    "Just as we observed earlier,", "By contrast,",
    "Relative to the global average,", "When measured against the standard,",
    "Compared to traditional approaches,", "Unlike the conventional wisdom,",
    "In much the same way as before,", "Against all expectations,",
    "Far more effectively than anticipated,", "Much less frequently than assumed,",
    "In stark contrast to the earlier findings,", "Mirroring trends seen elsewhere,",
    "When placed alongside international benchmarks,", "Just as notable as the first case,",
]

EXCLAMATION_OPENERS = [
    "What a wonderful", "What an interesting", "How remarkable that",
    "It is amazing how", "How surprising that", "What a great",
    "How impressive that", "What a thoughtful", "It is incredible how",
    "How encouraging that", "What a creative", "How fascinating that",
    "What an extraordinary", "How refreshing to see", "What a brilliant",
    "How truly remarkable that", "What an unexpected", "How inspiring it is that",
    "What a remarkable turn of events — ", "How extraordinary it is that",
]

CONDITIONAL_MIDDLES = [
    "the results could be quite different next time.",
    "it would save a significant amount of time and effort.",
    "the team would be in a much stronger position.",
    "we would need to reconsider the entire approach.",
    "it is worth exploring the alternatives first.",
    "the outcome tends to be more reliable.",
    "communication usually improves across the board.",
    "people tend to feel more confident in their decisions.",
    "the benefits outweigh the short-term challenges.",
    "it becomes easier with consistent practice.",
    "the next steps become much clearer.",
    "everything else tends to fall into place naturally.",
    "the long-term impact could be substantial.",
    "the risk of failure drops considerably.",
    "we would likely see measurable improvement within weeks.",
    "the whole process becomes far less stressful.",
    "it opens the door to a range of new possibilities.",
    "the foundation is in place for sustained progress.",
    "collaboration becomes genuinely more productive.",
    "the experience is far more rewarding for everyone involved.",
]

NARRATIVE_MIDDLES = [
    "and that was when everything started to make sense.",
    "though nobody had expected it to turn out that way.",
    "which was something none of them had planned for.",
    "and by the time it was over, they all felt changed.",
    "even though the outcome was not what they had hoped for.",
    "and the decision they made that day stayed with them.",
    "while the rest of the group waited anxiously nearby.",
    "and somehow, that made all the difference.",
    "even if it was only for a brief moment.",
    "and from that point on, nothing was quite the same.",
    "which made the whole experience more meaningful.",
    "while others watched from a respectful distance.",
    "and the atmosphere shifted in a way that was hard to describe.",
    "despite the many obstacles that had come before.",
    "which surprised everyone who was there to witness it.",
    "and the memory of it stayed with them for a very long time.",
    "though the road to get there had been anything but straightforward.",
    "and what happened next was something none of them would forget.",
    "yet somehow, it was exactly what they had needed.",
    "and the silence that followed said more than words could.",
    "in a way that none of the plans had accounted for.",
    "and the weight of the moment was felt by everyone present.",
]

RHETORICAL_QUESTIONS = [
    "But who decides what is truly fair in situations like these?",
    "Is it not remarkable how much we take for granted every day?",
    "Have we ever really stopped to consider what progress actually costs?",
    "What would we do if the familiar suddenly became unavailable?",
    "Is it possible that the simplest solutions are the ones we overlook most?",
    "Can we honestly say we have done everything we could have?",
    "Does it not make you wonder how different things might have been?",
    "How often do we confuse being busy with being productive?",
    "Is convenience always worth the price we pay for it?",
    "Have we truly learned anything if the same mistakes keep repeating?",
    "What does success really mean if it comes at the expense of others?",
    "Are we listening as carefully as we think we are?",
    "Could the answer have been in front of us all along?",
    "How much of what we believe is shaped by what we have been told?",
    "Is it not strange how the small details are often the most significant?",
    "When did we stop asking the questions that really matter?",
    "Do we always know the difference between what we want and what we need?",
    "What would happen if we simply chose to do things differently?",
    "Is there not something powerful in admitting that we do not know?",
    "Can a single moment really change the direction of a life?",
]

APHORISMS = [
    "Patience is not the ability to wait, but the ability to keep a good attitude while waiting.",
    "The best time to start was yesterday; the second best time is today.",
    "Not all who wander are lost, but many who are lost are not wandering — they are standing still.",
    "What you practice in private, you will be rewarded for in public.",
    "Understanding begins where assumptions end.",
    "A goal without a plan is just a wish.",
    "The quality of your questions determines the quality of your answers.",
    "Clarity is not the absence of complexity — it is the discipline to navigate it.",
    "Wisdom is knowing the difference between a lesson and a punishment.",
    "The strongest structures are built on the most honest foundations.",
    "Progress and comfort rarely share the same timetable.",
    "You do not rise to the occasion; you fall to the level of your preparation.",
    "The loudest voice in the room is not always the most informed.",
    "A problem clearly stated is a problem half-solved.",
    "What we measure, we tend to manage — and what we ignore tends to grow.",
    "The gap between knowing and doing is wider than most people admit.",
    "Habits are the invisible architecture of daily life.",
    "Every expert was once a complete beginner who refused to give up.",
    "The way we speak to ourselves shapes the way we see everything else.",
    "Curiosity is the engine of achievement.",
    "The most dangerous assumption is the one you never think to question.",
    "Kindness costs nothing and yet is worth everything.",
]

ANECDOTE_OPENERS = [
    "A colleague once told me something that I have never forgotten.",
    "There is an old story about a teacher who asked her students one simple question.",
    "A few years ago, a small team of engineers faced what seemed like an impossible problem.",
    "Not long ago, a woman in a small town made a decision that changed everything.",
    "I once read about a researcher who stumbled upon a discovery entirely by accident.",
    "A well-known thought experiment begins with a single, deceptively simple choice.",
    "Someone I know once described a moment that perfectly illustrated this idea.",
    "The story goes that a young apprentice asked his mentor a question no one had dared to ask before.",
    "Years ago, a group of scientists set out to answer what seemed like an obvious question.",
    "An often-told story in that community involves a founder who almost gave up on the third day.",
    "There was once a small village where nobody agreed on anything — except one thing.",
    "I remember reading about a pilot who landed safely despite every system failing at once.",
]

IMPERATIVES = [
    "Take a moment to consider what you actually know versus what you merely assume.",
    "Think about the last time something surprised you and ask yourself why.",
    "Look at the problem from a completely different direction before settling on a solution.",
    "Pay attention to the small details — they often contain the most important information.",
    "Step back before responding and ask whether your first instinct is serving you well.",
    "Listen more carefully than you think you need to.",
    "Write down your three most important priorities and keep them somewhere visible.",
    "Consider who else might be affected before you make the final decision.",
    "Start with what you know and work outward from there.",
    "Before moving on, make sure the person in front of you feels genuinely heard.",
    "Treat every mistake as a source of data rather than a cause for shame.",
    "Revisit your assumptions at least once before presenting your conclusions.",
    "Speak clearly, listen actively, and follow through on what you commit to.",
    "Ask yourself whether you are solving the right problem before investing more time.",
    "Choose your words carefully — they carry more weight than you might realise.",
    "Approach unfamiliar situations with curiosity rather than judgment.",
]

HYPOTHETICALS = [
    "Imagine if every student had access to a mentor who believed in them unconditionally.",
    "Suppose the most difficult challenge you ever faced turned out to be the most valuable.",
    "What if the conventional approach had been questioned twenty years earlier?",
    "Imagine a world in which accurate information spread faster than misinformation.",
    "Suppose everyone involved had been given the same amount of information from the start.",
    "What if the only way forward was the one that felt the most uncertain?",
    "Picture a team where everyone felt genuinely safe to share an unpopular idea.",
    "Imagine if patience were treated as a skill to be practised rather than a personality trait.",
    "Suppose the data had told a completely different story — what would we have concluded?",
    "What if the decision that seemed too costly was actually the least expensive in the long run?",
    "Imagine if the loudest objection turned out to have the most merit.",
    "Suppose the simplest explanation had been correct all along.",
    "What if consistency mattered more than brilliance in every domain of life?",
    "Picture a city designed entirely around the needs of pedestrians.",
    "Suppose the limits we believe in are the ones we have simply never tested.",
]

REPORTED_SPEECH_STARTERS = [
    "According to recent reports,", "Researchers have suggested that",
    "The report concluded that", "Several experts have argued that",
    "A spokesperson confirmed that", "The committee noted that",
    "Studies have indicated that", "Witnesses described how",
    "Officials have stated that", "Analysts believe that",
    "Sources close to the matter say that", "The findings suggest that",
    "It was reported this week that", "The review panel confirmed that",
    "Leading voices in the field have warned that",
    "The data indicates that", "A recent survey found that",
    "Local authorities have confirmed that",
]

CAUSAL_CONNECTORS = [
    "which ultimately led to", "and as a direct result,",
    "triggering a chain of events that", "which in turn caused",
    "setting off a sequence of outcomes that", "and the knock-on effect was that",
    "which brought about a situation in which", "eventually resulting in",
    "and that, in turn, meant that", "causing a shift that",
]

SENSORY_OPENERS = [
    "The smell of rain on warm concrete filled the air.",
    "There was a faint hum of activity coming from the next room.",
    "The sharp sound of the bell cut through the morning quiet.",
    "A warm golden light settled over the courtyard in the late afternoon.",
    "The texture of the old paper told its own story.",
    "There was a stillness to the air that felt oddly purposeful.",
    "The chill in the corridor made everyone move a little faster.",
    "Every surface in the room seemed to absorb the low winter light.",
    "The distant sound of traffic faded as they stepped inside.",
    "A sudden gust of wind sent papers scattering across the table.",
    "The familiar scent of coffee drifted through the office.",
    "The creak of the floorboard gave away exactly where she was standing.",
    "A bright shaft of sunlight crossed the floor and reached the opposite wall.",
    "The low murmur of conversation filled every corner of the hall.",
    "There was something about the texture of the morning that felt different.",
]

DEFINITION_OPENERS = [
    "The term refers to", "By definition,", "In simple terms,",
    "What we mean by this is", "The concept describes",
    "At its core, the idea means", "This can be understood as",
    "The word originally meant", "Technically speaking,",
    "In the strictest sense,", "The phrase is often used to describe",
    "Broadly defined,", "The notion encompasses",
]

DEFINITION_PHRASES = [
    "the ability to adapt quickly to changing circumstances without losing sight of the goal.",
    "a systematic approach to solving problems by breaking them into manageable components.",
    "the process of gathering evidence before drawing a conclusion.",
    "a way of organising information so that it can be retrieved and used efficiently.",
    "the recognition that multiple perspectives can each contain partial truths.",
    "a commitment to doing the right thing even when it is inconvenient.",
    "the practice of revisiting assumptions in light of new information.",
    "the capacity to communicate complex ideas in a way that is accessible to a broad audience.",
    "the discipline of distinguishing between what is urgent and what is important.",
    "a collaborative effort in which the contributions of each participant build on those of others.",
    "a framework for evaluating the long-term consequences of short-term decisions.",
    "the habit of reflecting on one's own thinking and looking for gaps in reasoning.",
]

NEWS_HEADLINE_STARTERS = [
    "In a development that has surprised many observers,",
    "Officials announced this week that",
    "A new report has confirmed that",
    "Campaigners have called for change after",
    "Experts are divided over",
    "A landmark study has found that",
    "In a decision welcomed by many,",
    "Community leaders have urged action following",
    "A growing number of voices are calling for",
    "New data has shed light on",
    "An unexpected turn of events saw",
    "Authorities are reviewing policy after",
    "Demand is rising for",
    "A breakthrough has been reported in",
    "Concerns have been raised about",
]

FUTURE_STARTERS = [
    "In the years ahead,", "By the end of the decade,",
    "Once the transition is complete,", "Looking further into the future,",
    "If current trends continue,", "Over the next generation,",
    "Within the next five years,", "As technology advances,",
    "Before long,", "Sooner than many expect,",
    "When the next phase begins,", "As we move forward,",
    "Eventually,", "In the not-too-distant future,",
    "Once the groundwork is laid,", "As the situation evolves,",
]

PROVERB_TWISTS = [
    "Patience may be a virtue, but so is knowing when to act.",
    "Every silver lining has a cloud — the skill is knowing when to look past it.",
    "A stitch in time saves nine, though finding the time is often the harder part.",
    "Out of sight is not always out of mind — sometimes it is precisely the opposite.",
    "Two heads are better than one, provided both are genuinely listening.",
    "The early bird gets the worm, but the second mouse gets the cheese.",
    "Actions speak louder than words, except when the words are carefully chosen.",
    "Practice makes perfect, though only if you are practising the right things.",
    "The road less travelled is not always better — sometimes it is less travelled for good reason.",
    "Fortune favours the prepared, not just the bold.",
    "You cannot pour from an empty cup — which is why rest is not a luxury.",
    "The grass is greener where it is watered, not simply where you are not standing.",
    "Slow and steady wins the race, unless the race requires urgency.",
    "Where there is a will, there is a way — but sometimes the will needs to be rebuilt first.",
]

REFLECTION_STARTERS = [
    "Looking back,", "In hindsight,", "Reflecting on that period,",
    "With the benefit of experience,", "Thinking about it now,",
    "On reflection,", "When I consider what happened,",
    "After all this time,", "Stepping back and looking at the bigger picture,",
    "Having seen this play out many times,", "Now that the dust has settled,",
    "From a distance,", "With fresh eyes,", "Re-examining the evidence,",
]

ANALOGY_STARTERS = [
    "Think of it like", "It is much like", "In the same way that",
    "Just as", "The process resembles", "It works a lot like",
    "Much in the way that", "Consider how", "Imagine it as",
    "This is similar to the way", "The analogy that fits best is",
    "As with", "The principle mirrors that of",
]

ANALOGY_BODIES = [
    "a foundation holds up a building — without it, even the best work above will eventually fail.",
    "a map does not create the terrain, but it makes navigating it far more manageable.",
    "a thermostat adjusts to changing conditions without needing to be told each time.",
    "a seed requires the right environment before it can reach its full potential.",
    "an orchestra where every section plays its part without needing to play louder than the others.",
    "a garden — it takes regular attention and patience before the results are visible.",
    "a mirror reflecting not just what is there, but what has always been there unnoticed.",
    "a well-worn path that becomes smoother and faster the more it is used.",
    "water finding the route of least resistance without stopping to consider the alternatives.",
    "a conversation where the most important information is often in what is left unsaid.",
    "a language everyone eventually understands, though the fluency takes time to develop.",
    "a bridge that connects two places most people assumed were too far apart to reach.",
]

ENUMERATION_OPENERS = [
    "There are three things worth remembering here:",
    "Several factors contribute to this outcome:",
    "The key elements are straightforward:",
    "A few distinct patterns emerge from this:",
    "The main reasons for this can be grouped as follows:",
    "What makes this work can be broken into clear parts:",
    "There are a handful of principles that consistently apply:",
    "The evidence points to a small number of core drivers:",
]

ENUMERATION_LISTS = [
    "consistency, clarity, and a willingness to revisit assumptions.",
    "the quality of the initial planning, the flexibility to adapt, and the discipline to follow through.",
    "preparation, presence, and the ability to listen before responding.",
    "access to accurate information, the confidence to act on it, and the support to do so.",
    "a clear goal, a realistic timeline, and honest communication between everyone involved.",
    "awareness of the problem, motivation to address it, and the resources to do so effectively.",
    "a stable environment, regular feedback, and a genuine commitment to learning.",
    "trust, transparency, and a shared sense of purpose.",
    "good data, good judgment, and good timing.",
    "curiosity, rigour, and a tolerance for uncertainty.",
]

# ════════════════════════════════════════════════════════════════════════════
# DOMAIN LEXICONS  (28 domains — 12 original + 12 new)
# ════════════════════════════════════════════════════════════════════════════

DOMAINS: dict[str, dict] = {

    "school": {
        "subjects": [
            "The student", "Our teacher", "The class", "My friend",
            "Every pupil", "The librarian", "A group of students",
            "The school principal", "Our math teacher", "The new kid",
            "The substitute teacher", "The study group", "Our history teacher",
            "The school counsellor", "A dedicated student",
            "The school's debate team", "The new head of year",
            "A first-year student", "The after-school club",
        ],
        "verbs_b": ["finished", "read", "wrote", "asked", "helped", "joined", "studied", "answered"],
        "verbs_i": ["submitted", "reviewed", "discussed", "prepared", "explained", "revised", "debated", "presented"],
        "verbs_a": ["analysed", "evaluated", "synthesised", "interpreted", "critiqued", "contextualised", "formulated"],
        "objects_b": [
            "the homework", "a book", "the assignment", "the quiz",
            "a short story", "the worksheet", "the spelling test", "a poster",
        ],
        "objects_i": [
            "the science project", "an essay on climate", "the group presentation",
            "the reading comprehension test", "the class notes",
            "a research summary", "the mid-term exam",
        ],
        "objects_a": [
            "a comparative analysis of the two theories", "the literary critique",
            "a structured argument for the debate", "an annotated bibliography",
            "a peer-reviewed research proposal",
        ],
        "extras_b": [
            "before lunch.", "on time.", "with a smile.", "during class.",
            "together with a partner.", "after the bell rang.", "in the library.",
        ],
        "extras_i": [
            "after the teacher explained the concept.", "by following the rubric carefully.",
            "ahead of the deadline.", "with very clear handwriting.",
            "using the resources provided.",
        ],
        "extras_a": [
            "demonstrating a nuanced understanding of the subject matter.",
            "referencing multiple academic sources.",
            "with a well-structured introduction and conclusion.",
            "incorporating primary and secondary research.",
        ],
        "questions_b": [
            "Can you help me with my homework?",
            "What page are we on?",
            "Is this going to be on the test?",
            "Can I borrow a pencil?",
            "When is the assignment due?",
            "Did we have homework last night?",
            "What does this word mean?",
            "Is the library open after school?",
        ],
        "questions_i": [
            "Could you explain the difference between metaphor and simile?",
            "How do we calculate the area of a triangle?",
            "What are the main causes of the First World War?",
            "Is the essay supposed to be in MLA or APA format?",
            "How should we structure our group presentation?",
            "Could you recommend some reliable sources for this topic?",
        ],
        "questions_a": [
            "How does the author use irony to challenge social norms in the text?",
            "What epistemological assumptions underlie this research methodology?",
            "Can you elaborate on the relationship between entropy and information theory?",
            "How do post-structuralist theories inform our reading of this novel?",
        ],
    },

    "technology": {
        "subjects": [
            "The software", "Our app", "The developer", "The new update",
            "The operating system", "A cloud server", "The algorithm",
            "The database", "The API", "The user interface",
            "The firmware", "Our engineering team", "The open-source library",
            "The machine learning model", "The security system",
            "The DevOps pipeline", "The neural network", "The data scientist",
        ],
        "verbs_b": ["crashed", "updated", "loaded", "opened", "saved", "fixed", "restarted", "downloaded"],
        "verbs_i": ["processed", "encrypted", "optimised", "deployed", "integrated", "compiled", "debugged", "migrated"],
        "verbs_a": [
            "asynchronously synchronised", "containerised", "load-balanced",
            "refactored", "orchestrated", "horizontally scaled", "auto-sharded",
            "fine-tuned", "benchmarked against production baselines",
        ],
        "objects_b": [
            "the file", "the app", "the website", "the password", "the settings",
            "the Wi-Fi", "the screen",
        ],
        "objects_i": [
            "the user data", "the API response", "the network connection",
            "the error logs", "the software package",
            "the authentication token", "the build pipeline",
        ],
        "objects_a": [
            "the distributed microservices architecture",
            "the real-time data pipeline",
            "the machine learning inference endpoint",
            "the containerised deployment workflow",
            "the event-driven message broker topology",
        ],
        "extras_b": [
            "automatically.", "in seconds.", "without any errors.",
            "after a quick restart.", "on the new device.",
        ],
        "extras_i": [
            "using the latest security patch.", "across multiple platforms.",
            "without interrupting the user experience.", "in the background.",
            "following the technical documentation.",
        ],
        "extras_a": [
            "leveraging a reactive event-driven architecture.",
            "with zero-downtime blue-green deployment.",
            "through automated CI/CD pipelines.",
            "using infrastructure-as-code principles.",
        ],
        "questions_b": [
            "Why is my phone so slow?",
            "How do I turn off notifications?",
            "Did you update the app yet?",
            "Can I use this software for free?",
            "Where do I find the settings?",
            "How do I connect to the Wi-Fi?",
        ],
        "questions_i": [
            "What is the difference between RAM and storage?",
            "How does end-to-end encryption work?",
            "Why does the server keep timing out?",
            "Is it safe to use public Wi-Fi for online banking?",
            "What is the benefit of using version control?",
            "What are the main differences between REST and GraphQL?",
        ],
        "questions_a": [
            "What are the trade-offs between eventual consistency and strong consistency in distributed systems?",
            "How does gradient descent optimise neural network weights during backpropagation?",
            "What are the implications of using a monolithic versus microservices architecture at scale?",
            "How does the CAP theorem constrain distributed database design?",
        ],
    },

    "healthcare": {
        "subjects": [
            "The doctor", "The nurse", "The patient", "My family",
            "The hospital staff", "A pharmacist", "The specialist",
            "Our health clinic", "The paramedic", "The receptionist",
            "The physiotherapist", "A nutritionist", "The surgeon",
            "Our family doctor", "The mental health counsellor",
            "The occupational therapist", "The triage nurse",
            "The clinical psychologist",
        ],
        "verbs_b": ["checked", "helped", "visited", "rested", "drank", "called", "reminded", "felt"],
        "verbs_i": ["prescribed", "examined", "monitored", "advised", "recommended", "referred", "reviewed"],
        "verbs_a": [
            "diagnosed", "administered", "evaluated", "coordinated",
            "assessed the prognosis of", "formulated a management plan for",
            "implemented evidence-based protocols for",
        ],
        "objects_b": [
            "the patient", "some water", "a vitamin tablet", "a bandage",
            "the medicine", "a healthy meal", "the appointment",
        ],
        "objects_i": [
            "the blood pressure", "the test results", "the treatment plan",
            "the allergy report", "the medical history",
            "the follow-up appointment", "the dosage instructions",
        ],
        "objects_a": [
            "the multimodal pain management protocol",
            "the post-operative rehabilitation schedule",
            "the differential diagnosis",
            "the evidence-based clinical guidelines",
            "the comorbidity risk stratification framework",
        ],
        "extras_b": [
            "every morning.", "with a glass of water.", "after meals.",
            "at the local clinic.", "before going to bed.",
        ],
        "extras_i": [
            "following the standard care protocol.",
            "after reviewing the lab results.", "twice a day for two weeks.",
            "based on the patient's history.",
        ],
        "extras_a": [
            "in accordance with the latest WHO clinical guidelines.",
            "incorporating patient-reported outcome measures.",
            "to minimise adverse drug interactions.",
            "within a multidisciplinary care team framework.",
        ],
        "questions_b": [
            "Are you feeling better today?",
            "Did you take your medicine this morning?",
            "Should I drink more water?",
            "Is it safe to exercise with a cold?",
            "Can I eat before the blood test?",
            "How long should I rest?",
        ],
        "questions_i": [
            "What are the common side effects of this medication?",
            "How long does it take for antibiotics to work?",
            "Should I see a specialist for this condition?",
            "Is this rash something to be concerned about?",
            "What lifestyle changes can help manage high blood pressure?",
        ],
        "questions_a": [
            "What is the recommended first-line treatment for type 2 diabetes in adults with renal impairment?",
            "How do immunosuppressive therapies affect vaccine efficacy in transplant patients?",
            "What biomarkers are most predictive of cardiovascular risk in asymptomatic patients?",
        ],
    },

    "travel": {
        "subjects": [
            "The traveller", "Our family", "My friend", "The tour guide",
            "A group of tourists", "The pilot", "The hotel staff",
            "The backpacker", "We", "The passengers",
            "The travel agent", "An experienced explorer", "Our road-trip group",
            "A solo adventurer", "The cruise director",
        ],
        "verbs_b": ["visited", "packed", "arrived", "booked", "enjoyed", "explored", "rested", "walked"],
        "verbs_i": ["navigated", "discovered", "photographed", "checked in", "departed", "planned", "researched"],
        "verbs_a": [
            "meticulously planned", "immersed themselves in",
            "cross-culturally experienced", "traversed",
            "ethnographically documented",
        ],
        "objects_b": [
            "the beach", "the airport", "the hotel", "a new city",
            "the local market", "the train station",
        ],
        "objects_i": [
            "the ancient ruins", "a scenic mountain trail", "the historic city centre",
            "a traditional village", "the coastal road",
            "a local cooking class", "the national museum",
        ],
        "objects_a": [
            "the geopolitical complexities of the border region",
            "the intangible cultural heritage of the indigenous community",
            "the ecological diversity of the national reserve",
        ],
        "extras_b": [
            "last summer.", "on a sunny afternoon.", "for the first time.",
            "with great excitement.", "as a family.",
        ],
        "extras_i": [
            "during the off-peak season.", "with a detailed travel itinerary.",
            "after months of careful planning.", "using only public transport.",
        ],
        "extras_a": [
            "while documenting sustainable tourism practices.",
            "drawing on ethnographic field research.",
            "in collaboration with local conservation groups.",
        ],
        "questions_b": [
            "Where are we going next?",
            "Did you book the hotel yet?",
            "How long is the flight?",
            "Is the beach nearby?",
            "What should I pack for the trip?",
            "Do we need travel insurance?",
        ],
        "questions_i": [
            "What is the best time of year to visit Japan?",
            "Do I need a visa to travel to that country?",
            "Which airline has the best baggage allowance?",
            "Are there any travel advisories I should know about?",
            "What is the most affordable way to travel between cities?",
        ],
        "questions_a": [
            "How do geopolitical tensions affect international tourism flows in developing economies?",
            "What role does overtourism play in the degradation of UNESCO World Heritage Sites?",
            "How can sustainable travel practices be effectively incentivised at a policy level?",
        ],
    },

    "environment": {
        "subjects": [
            "Scientists", "Local communities", "The government", "Our school",
            "Volunteers", "Environmental groups", "Young activists",
            "Researchers", "The organisation", "Citizens",
            "Conservation workers", "Student campaigners", "International NGOs",
            "Marine biologists", "Urban planners",
        ],
        "verbs_b": ["planted", "cleaned", "saved", "recycled", "protected", "collected", "helped", "shared"],
        "verbs_i": ["monitored", "conserved", "campaigned for", "measured", "reduced", "reported on", "analysed"],
        "verbs_a": [
            "modelled the long-term impact of", "advocated for systemic change in",
            "quantified the carbon footprint of", "evaluated the biodiversity of",
            "developed mitigation strategies for",
        ],
        "objects_b": [
            "the trees", "the beach", "the park", "the river",
            "the plastic waste", "the local garden",
        ],
        "objects_i": [
            "the air quality", "the coral reef", "the wildlife habitat",
            "the carbon emissions", "the local ecosystem",
            "the water table", "the endangered species",
        ],
        "objects_a": [
            "the anthropogenic impact on global nitrogen cycles",
            "the interplay between deforestation and regional precipitation patterns",
            "the effectiveness of carbon offset programmes",
            "the resilience of urban green infrastructure under climate stress",
        ],
        "extras_b": [
            "this weekend.", "at the local park.", "every day.",
            "with friends and family.", "as part of a school project.",
        ],
        "extras_i": [
            "as part of a national campaign.", "over the past decade.",
            "using satellite data.", "in partnership with local authorities.",
        ],
        "extras_a": [
            "using longitudinal remote sensing datasets.",
            "in the context of the Paris Agreement targets.",
            "drawing on peer-reviewed environmental science.",
        ],
        "questions_b": [
            "Why is it important to recycle?",
            "How can we help protect animals?",
            "Is it bad to leave the tap running?",
            "Why are trees so important?",
            "What happens to our rubbish?",
            "How do we keep the ocean clean?",
        ],
        "questions_i": [
            "What are the main causes of climate change?",
            "How does deforestation affect rainfall patterns?",
            "What can individuals do to reduce their carbon footprint?",
            "Why are coral reefs disappearing?",
            "How can renewable energy replace fossil fuels?",
        ],
        "questions_a": [
            "How does ocean acidification interact with marine biodiversity at the ecosystem level?",
            "What are the limitations of current carbon capture and storage technologies?",
            "How do tipping points in the climate system affect long-range forecasting models?",
        ],
    },

    "family": {
        "subjects": [
            "My mum", "Our family", "My little sister", "Dad", "Grandma",
            "My brother", "We", "Our parents", "My aunt", "The whole family",
            "My cousin", "Grandpa", "My older sister", "Our relatives",
            "My nephew", "My niece", "Our next-door neighbours",
        ],
        "verbs_b": ["made", "ate", "laughed", "helped", "played", "hugged", "visited", "cooked", "shared"],
        "verbs_i": ["organised", "celebrated", "discussed", "supported", "arranged", "planned", "gathered"],
        "verbs_a": [
            "navigated the complexities of", "facilitated open dialogue about",
            "collectively decided on", "thoughtfully considered",
            "carefully balanced the competing needs of",
        ],
        "objects_b": [
            "dinner", "a cake", "a board game", "the garden",
            "a family photo", "a bedtime story", "the picnic",
        ],
        "objects_i": [
            "a weekend trip", "the household budget", "the family reunion",
            "a tough conversation", "the holiday schedule",
            "a home improvement project",
        ],
        "objects_a": [
            "the intergenerational dynamics within the household",
            "long-term financial planning for the family",
            "the emotional impact of relocation on younger children",
        ],
        "extras_b": [
            "on Sunday evening.", "after dinner.", "with lots of joy.",
            "for the first time in months.", "together at home.",
        ],
        "extras_i": [
            "during the school holidays.", "despite everyone's busy schedule.",
            "with a lot of care and consideration.", "as a family tradition.",
        ],
        "extras_a": [
            "in light of recent economic pressures.",
            "drawing on open and respectful communication.",
            "within the context of changing family structures.",
        ],
        "questions_b": [
            "What are we having for dinner?",
            "Can I play with my brother?",
            "Are we going to grandma's house this weekend?",
            "Can we get a pet?",
            "When will mum be home?",
            "Can we watch a film tonight?",
        ],
        "questions_i": [
            "How do you balance work and family life?",
            "What is your favourite family tradition?",
            "How do you handle disagreements at home?",
            "What do you do for school holidays?",
            "How do you stay in touch with relatives who live far away?",
        ],
        "questions_a": [
            "How do shifting family structures affect child development outcomes?",
            "In what ways does intergenerational wealth transfer perpetuate socioeconomic inequality?",
            "How do cultural expectations around family roles shape individual identity formation?",
        ],
    },

    "workplace": {
        "subjects": [
            "The manager", "Our department", "A senior colleague", "The intern",
            "The HR team", "Our team leader", "The board of directors",
            "A project coordinator", "The new hire", "The chief executive",
            "The remote team", "A freelance contractor", "The department head",
        ],
        "verbs_b": ["sent", "attended", "drafted", "replied", "reviewed", "submitted", "completed", "called"],
        "verbs_i": ["coordinated", "presented", "delegated", "analysed", "negotiated", "restructured", "onboarded"],
        "verbs_a": [
            "strategically repositioned", "operationally transformed",
            "systematically evaluated", "cross-functionally aligned",
            "institutionally embedded", "iteratively improved",
        ],
        "objects_b": [
            "the email", "the form", "the meeting notes", "the invoice",
            "the report", "the spreadsheet", "the presentation",
        ],
        "objects_i": [
            "the project proposal", "the quarterly review",
            "the client deliverable", "the performance targets",
            "the team's workflow", "the budget forecast",
        ],
        "objects_a": [
            "the enterprise-wide change management strategy",
            "the organisational capability framework",
            "the cross-departmental knowledge transfer protocol",
            "the governance and accountability structure",
        ],
        "extras_b": [
            "before the end of day.", "on time.", "without any errors.",
            "after the team meeting.", "via email.",
        ],
        "extras_i": [
            "following the internal review process.", "within budget and on schedule.",
            "in collaboration with the wider team.", "after gathering stakeholder input.",
        ],
        "extras_a": [
            "leveraging data-driven decision-making frameworks.",
            "in alignment with the organisation's strategic objectives.",
            "through a structured programme of change management interventions.",
        ],
        "questions_b": [
            "Can you send me that file?",
            "What time is the meeting?",
            "Did you finish the report?",
            "Is the printer working today?",
            "Who should I contact about this?",
        ],
        "questions_i": [
            "Could you clarify the deadline for this project?",
            "What are the key deliverables for Q3?",
            "How should we handle the client's feedback?",
            "Can we reschedule Thursday's call?",
            "What is the process for requesting annual leave?",
        ],
        "questions_a": [
            "How should we align our OKRs with the broader organisational strategy for next fiscal year?",
            "What governance framework best supports decentralised decision-making in a scaling enterprise?",
            "How do we measure the ROI of our internal knowledge management system?",
        ],
    },

    "emotions": {
        "subjects": [
            "She", "He", "They", "I", "My friend", "The child",
            "Everyone in the room", "The whole group", "We", "Most people",
            "The teenager", "My classmate", "The young woman",
            "The quiet one in the corner", "My older colleague",
        ],
        "verbs_b": ["felt", "smiled", "cried", "laughed", "got scared", "was happy", "seemed", "appeared"],
        "verbs_i": ["struggled with", "expressed", "overcame", "reflected on", "dealt with", "opened up about"],
        "verbs_a": [
            "grappled with the emotional complexity of",
            "articulated the nuanced interplay between",
            "processed the underlying psychological dimensions of",
            "navigated the dissonance between",
        ],
        "objects_b": [
            "a little nervous", "very excited", "quite sad",
            "surprisingly calm", "really happy", "a bit confused", "quite proud",
        ],
        "objects_i": [
            "a deep sense of uncertainty", "overwhelming anxiety",
            "unexpected feelings of loneliness", "a quiet sense of pride",
            "a growing sense of confidence",
        ],
        "objects_a": [
            "the cognitive dissonance arising from conflicting values",
            "the long-term psychological effects of repeated social exclusion",
            "the emotional labour involved in caregiving roles",
            "the psychological toll of sustained uncertainty",
        ],
        "extras_b": [
            "when the results came out.", "on the first day of school.",
            "after hearing the news.", "during the performance.",
            "at the birthday party.",
        ],
        "extras_i": [
            "after weeks of uncertainty.", "despite trying to stay positive.",
            "in front of a large audience.", "while helping a close friend.",
        ],
        "extras_a": [
            "within the context of prolonged occupational stress.",
            "as examined through the lens of attachment theory.",
            "drawing on recent findings in affective neuroscience.",
        ],
        "questions_b": [
            "Are you feeling okay today?",
            "Why does she look so sad?",
            "Did he cheer up after lunch?",
            "Is it normal to feel nervous before a test?",
            "Why are you smiling so much?",
            "Are you excited about the trip?",
        ],
        "questions_i": [
            "How do you manage stress during busy periods?",
            "What helps you feel better when you are upset?",
            "Why do some people find it hard to express their feelings?",
            "How can we support a friend going through a tough time?",
        ],
        "questions_a": [
            "How does emotional regulation develop across different stages of childhood?",
            "What neurological mechanisms underpin the experience of empathy?",
            "How do cultural norms shape the expression and suppression of emotions?",
        ],
    },

    "hobbies": {
        "subjects": [
            "She", "My friend", "The artist", "He", "Our club",
            "The photographer", "I", "A small group", "The team", "They",
            "The pottery class", "Our film group", "An enthusiastic beginner",
            "The amateur astronomer", "The local chess club",
        ],
        "verbs_b": ["painted", "played", "read", "baked", "drew", "sang", "knitted", "collected", "danced"],
        "verbs_i": ["practised", "designed", "performed", "composed", "illustrated", "recorded", "curated"],
        "verbs_a": [
            "meticulously crafted", "conceptually developed", "systematically refined",
            "collaboratively produced", "innovatively reimagined",
        ],
        "objects_b": [
            "a picture", "the guitar", "a short story", "some cookies",
            "a photo", "a simple melody", "a friendship bracelet",
        ],
        "objects_i": [
            "a landscape portrait", "a new song", "a short documentary",
            "an intricate model", "a detailed sketch",
            "a handmade piece of furniture",
        ],
        "objects_a": [
            "a multimedia installation exploring themes of identity",
            "a long-form narrative combining photography and prose",
            "a symphonic arrangement for a community orchestra",
        ],
        "extras_b": [
            "after school.", "on a rainy afternoon.", "with great enthusiasm.",
            "for the school art show.", "just for fun.",
        ],
        "extras_i": [
            "over several weekends.", "as part of a local exhibition.",
            "inspired by everyday life.", "with surprising technical skill.",
        ],
        "extras_a": [
            "as part of a residency programme exploring cultural memory.",
            "drawing on postmodern aesthetic theory.",
            "through an iterative process of experimentation and critique.",
        ],
        "questions_b": [
            "Do you have any hobbies?",
            "What do you like to do after school?",
            "Can you teach me how to draw?",
            "Is painting difficult to learn?",
            "Do you play any musical instruments?",
        ],
        "questions_i": [
            "How long have you been playing the piano?",
            "Where do you find inspiration for your artwork?",
            "What equipment do you need to start photography?",
            "Have you ever performed in front of an audience?",
            "What is the hardest part of learning a new craft?",
        ],
        "questions_a": [
            "How does the concept of flow state apply to sustained creative practice?",
            "In what ways does amateur participation in the arts contribute to community well-being?",
            "How has digital technology transformed the boundaries between professional and amateur artistic production?",
        ],
    },

    "science": {
        "subjects": [
            "Scientists", "The experiment", "Researchers", "The lab team",
            "A new study", "The data", "The hypothesis", "Our class",
            "The observation", "The model", "A team of physicists", "The simulation",
            "The field researchers", "The peer reviewers",
        ],
        "verbs_b": ["showed", "found", "tested", "measured", "observed", "studied", "proved", "recorded"],
        "verbs_i": ["demonstrated", "analysed", "confirmed", "explored", "documented", "validated", "replicated"],
        "verbs_a": [
            "empirically validated", "computationally modelled",
            "statistically corroborated", "systematically evaluated",
            "longitudinally tracked",
        ],
        "objects_b": [
            "that plants need sunlight", "how rainbows form",
            "the boiling point of water", "why the moon has phases",
            "how magnets work",
        ],
        "objects_i": [
            "the relationship between temperature and reaction rate",
            "how vaccines stimulate the immune system",
            "the structure of a DNA molecule",
            "the effect of light on photosynthesis",
        ],
        "objects_a": [
            "the nonlinear dynamics of chaotic systems",
            "the quantum entanglement properties of paired particles",
            "the epigenetic mechanisms regulating gene expression",
            "the thermodynamic constraints on biological energy transfer",
        ],
        "extras_b": [
            "in a simple classroom experiment.", "using basic materials.",
            "for the first time.", "with very clear results.",
        ],
        "extras_i": [
            "using a controlled experimental design.",
            "after collecting data over several months.",
            "with a statistically significant result.",
            "under carefully monitored conditions.",
        ],
        "extras_a": [
            "through a peer-reviewed double-blind randomised controlled trial.",
            "using high-resolution cryo-electron microscopy.",
            "via multi-scale computational simulation.",
        ],
        "questions_b": [
            "Why is the sky blue?",
            "How do plants grow?",
            "What makes a rainbow appear?",
            "Why do we need oxygen to breathe?",
            "What is gravity?",
        ],
        "questions_i": [
            "How does the process of natural selection drive evolution?",
            "What is the difference between nuclear fission and fusion?",
            "How do black holes form?",
            "What causes the tides to rise and fall?",
        ],
        "questions_a": [
            "What are the thermodynamic implications of Maxwell's demon thought experiment?",
            "How does the renormalisation group explain phase transitions in statistical mechanics?",
            "What evidence supports the multiverse interpretation of quantum mechanics?",
        ],
    },

    "food": {
        "subjects": [
            "The chef", "Our family", "My mum", "The restaurant",
            "A home cook", "The bakery", "My friend", "The street vendor",
            "The caterer", "A passionate foodie", "The cooking class",
            "Our school canteen", "The sous-chef", "A food blogger",
        ],
        "verbs_b": ["cooked", "baked", "tasted", "ordered", "shared", "enjoyed", "prepared", "served", "tried"],
        "verbs_i": ["marinated", "caramelised", "seasoned", "garnished", "plated", "slow-cooked", "fermented", "infused"],
        "verbs_a": [
            "deconstructed the flavour profile of", "meticulously crafted",
            "artisanally produced", "sourced sustainably for",
            "developed a farm-to-table concept around",
        ],
        "objects_b": [
            "a simple pasta dish", "some scrambled eggs", "a sandwich",
            "a bowl of soup", "a fruit salad", "some toast",
        ],
        "objects_i": [
            "a three-course dinner", "a slow-roasted lamb dish",
            "a freshly baked sourdough loaf", "a Thai green curry",
            "a seasonal vegetable stew",
        ],
        "objects_a": [
            "a tasting menu with molecular gastronomy techniques",
            "a heritage grain fermentation programme",
            "an umami-layered broth using traditional Japanese dashi",
        ],
        "extras_b": [
            "for breakfast.", "at the dinner table.", "with the family.",
            "from scratch.", "as a treat.",
        ],
        "extras_i": [
            "using locally sourced ingredients.", "over a low heat for two hours.",
            "with a generous pinch of fresh herbs.", "following a traditional family recipe.",
        ],
        "extras_a": [
            "drawing on classical French culinary technique.",
            "while honouring the cultural origins of the dish.",
            "through a zero-waste kitchen philosophy.",
        ],
        "questions_b": [
            "What is for dinner tonight?",
            "Do you want some more soup?",
            "Can you pass the salt, please?",
            "Is this spicy?",
            "What is your favourite food?",
            "Did you eat already?",
        ],
        "questions_i": [
            "What is the best way to cook a perfect steak?",
            "How do you make bread dough rise properly?",
            "What makes sourdough different from regular bread?",
            "How do you balance sweet and sour flavours in cooking?",
            "What is the secret to a really good curry?",
        ],
        "questions_a": [
            "How do Maillard reactions differ from caramelisation at a chemical level?",
            "What role does emulsification play in achieving stable vinaigrettes and sauces?",
            "How do regional food traditions function as expressions of cultural identity?",
        ],
    },

    "weather": {
        "subjects": [
            "The weather", "A storm", "The forecast", "Heavy rainfall",
            "Thick fog", "A gentle breeze", "The heatwave",
            "Meteorologists", "The cold front", "A sudden downpour",
            "The snowstorm", "Warm temperatures", "The jet stream",
        ],
        "verbs_b": ["arrived", "started", "stopped", "changed", "covered", "cleared", "fell", "dropped"],
        "verbs_i": ["intensified", "disrupted", "delayed", "triggered", "settled", "swept through", "persisted"],
        "verbs_a": [
            "significantly impacted agricultural output across",
            "was attributed to a strengthening El Nino pattern over",
            "contributed to flash-flooding conditions throughout",
        ],
        "objects_b": [
            "the town", "the afternoon", "the picnic", "the sky",
            "the ground", "the park",
        ],
        "objects_i": [
            "the coastal areas", "the transport network", "the harvest season",
            "the outdoor event", "the flood-prone zones",
        ],
        "objects_a": [
            "the semi-arid zones of the southern region",
            "the regional hydrological cycle",
            "emergency flood response planning protocols",
        ],
        "extras_b": [
            "without any warning.", "all day long.", "by the afternoon.",
            "just before school.", "very suddenly.",
        ],
        "extras_i": [
            "after a long dry spell.", "bringing welcome relief.",
            "across several regions simultaneously.",
            "for the third consecutive week.",
        ],
        "extras_a": [
            "in line with revised IPCC scenario projections.",
            "as recorded by a network of automated weather stations.",
            "according to national meteorological authority data.",
        ],
        "questions_b": [
            "Is it going to rain today?",
            "Should I bring an umbrella?",
            "Why is it so cold today?",
            "Will it snow this winter?",
            "What is the weather like outside?",
        ],
        "questions_i": [
            "What causes a thunderstorm to form?",
            "How do meteorologists predict the weather so far in advance?",
            "Why do coastal areas have milder winters?",
            "What is the difference between climate and weather?",
        ],
        "questions_a": [
            "How does the Atlantic Meridional Overturning Circulation influence European climate patterns?",
            "What are the limitations of ensemble weather forecasting models beyond seven days?",
            "How does urban heat island effect compound heatwave severity in densely populated cities?",
        ],
    },

    "shopping": {
        "subjects": [
            "The customer", "A shopper", "The store assistant", "My mum",
            "The manager", "We", "A regular buyer", "The online retailer",
            "The cashier", "A first-time buyer",
            "Our neighbourhood market", "The discount store",
            "The luxury brand", "A deal hunter",
        ],
        "verbs_b": ["bought", "found", "chose", "paid", "returned", "asked", "tried on", "checked"],
        "verbs_i": ["browsed", "negotiated", "exchanged", "ordered", "reviewed", "tracked", "refunded"],
        "verbs_a": [
            "leveraged a dynamic pricing strategy for",
            "analysed the consumer demand pattern behind",
            "curated a personalised recommendation engine for",
        ],
        "objects_b": [
            "a new pair of shoes", "some groceries", "a birthday gift",
            "a book", "a winter coat", "some stationery",
        ],
        "objects_i": [
            "the best deal on a laptop", "a high-quality kitchen appliance",
            "an affordable gym membership",
            "a premium skincare product", "a seasonal sale item",
        ],
        "objects_a": [
            "a complex omnichannel customer journey",
            "the algorithmic personalisation of e-commerce recommendations",
            "a sustainable supply chain with ethical sourcing standards",
        ],
        "extras_b": [
            "at the local market.", "with a discount.", "online.",
            "before the sale ended.", "as a surprise.",
        ],
        "extras_i": [
            "after reading multiple reviews.", "during the holiday sale.",
            "using a price comparison website.", "with a loyalty points card.",
        ],
        "extras_a": [
            "based on predictive demand modelling.",
            "optimised through real-time inventory management.",
            "drawing on behavioural economics principles.",
        ],
        "questions_b": [
            "How much does this cost?",
            "Do you have this in a different size?",
            "Is there a discount on this?",
            "Can I pay by card?",
            "Is this item in stock?",
        ],
        "questions_i": [
            "What is the return policy for online purchases?",
            "How do I apply a discount code at checkout?",
            "Is this product covered by a warranty?",
            "How long does standard delivery take?",
        ],
        "questions_a": [
            "How do dark patterns in e-commerce UX influence consumer spending behaviour?",
            "What are the supply chain implications of fast fashion for environmental sustainability?",
            "How does dynamic pricing affect consumer trust and brand loyalty over time?",
        ],
    },

    "gaming": {
        "subjects": [
            "The player", "Our team", "My brother", "The gamer",
            "A new character", "The online community", "The game developer",
            "A competitive player", "The streaming community", "My friend",
            "A speedrunner", "The tournament team", "An indie game studio",
            "The esports coach", "The level designer",
        ],
        "verbs_b": ["played", "won", "lost", "joined", "tried", "unlocked", "completed", "discovered"],
        "verbs_i": ["mastered", "streamed", "speedran", "customised", "coordinated", "competed in", "modded"],
        "verbs_a": [
            "analysed the game theory mechanics of",
            "deconstructed the narrative structure of",
            "systematically optimised the build configuration for",
            "critically evaluated the monetisation model of",
        ],
        "objects_b": [
            "the final level", "a new game mode", "the tutorial",
            "a hidden item", "the boss", "the first mission",
        ],
        "objects_i": [
            "the team strategy", "the character build", "the online tournament",
            "a world record speedrun", "a co-op campaign",
        ],
        "objects_a": [
            "the psychological impact of reward loops in live service games",
            "the ethical dimensions of loot box monetisation models",
            "the procedural generation algorithm underpinning the open world",
        ],
        "extras_b": [
            "on the weekend.", "after finishing homework.", "with a friend.",
            "for the first time.", "late at night.",
        ],
        "extras_i": [
            "after hours of practice.", "with a carefully planned strategy.",
            "during the global launch event.", "with impressive coordination.",
        ],
        "extras_a": [
            "drawing on game-theoretic decision frameworks.",
            "within the context of esports professionalisation.",
            "highlighting the growing influence of player communities on game design.",
        ],
        "questions_b": [
            "What game are you playing?",
            "Can I play too?",
            "Did you beat the boss yet?",
            "How do you unlock that character?",
            "Is this game free?",
        ],
        "questions_i": [
            "What is the most efficient build for this class?",
            "How do speedrunners find shortcuts in games?",
            "What makes a multiplayer game balanced?",
            "Is this game worth buying at full price?",
        ],
        "questions_a": [
            "How do Skinner box reward mechanisms in game design influence compulsive play behaviour?",
            "What distinguishes emergent gameplay from scripted narrative in open-world design?",
            "How has esports professionalisation changed the cultural perception of gaming?",
        ],
    },

    "internet": {
        "subjects": [
            "The website", "A content creator", "The social media platform",
            "An online community", "The streaming service", "My favourite blogger",
            "The search engine", "A viral post", "The newsletter author",
            "The podcast host", "A digital journalist", "The online forum",
            "The algorithm", "A fact-checking organisation",
        ],
        "verbs_b": ["posted", "shared", "watched", "liked", "commented", "searched", "followed", "downloaded"],
        "verbs_i": ["published", "live-streamed", "curated", "monetised", "collaborated", "fact-checked", "moderated"],
        "verbs_a": [
            "algorithmically amplified", "adversarially optimised",
            "platform-natively distributed", "crowdsourced and aggregated",
            "systematically analysed the engagement patterns of",
        ],
        "objects_b": [
            "a funny video", "a helpful tutorial", "a photo",
            "a short clip", "a comment", "a news article",
        ],
        "objects_i": [
            "a long-form essay", "a product review series",
            "a live Q&A session", "a newsletter on technology trends",
            "a community discussion thread",
        ],
        "objects_a": [
            "a decentralised content moderation policy",
            "the algorithmic bias embedded in recommendation systems",
            "the attention economy's impact on content quality",
        ],
        "extras_b": [
            "after school.", "on their phone.", "with lots of comments.",
            "in just a few minutes.", "every week.",
        ],
        "extras_i": [
            "to a global audience.", "with a strong community response.",
            "using accessible and engaging language.", "across multiple platforms.",
        ],
        "extras_a": [
            "navigating the tension between free expression and community safety.",
            "drawing on network science and information diffusion theory.",
            "within the regulatory framework of digital platform governance.",
        ],
        "questions_b": [
            "Have you seen that video everyone is talking about?",
            "How do I make my password stronger?",
            "Why is my internet so slow today?",
            "Can I watch that for free online?",
            "How do I block someone online?",
        ],
        "questions_i": [
            "How do content creators earn money online?",
            "What makes a video go viral?",
            "How do I stay safe from phishing emails?",
            "How do search engine algorithms decide what to show first?",
        ],
        "questions_a": [
            "How does personalisation-driven content delivery affect epistemic diversity at a population level?",
            "What are the regulatory challenges of governing cross-border disinformation campaigns?",
            "How do recommendation algorithms interact with extremism radicalisation pathways?",
        ],
    },

    "communication": {
        "subjects": [
            "The speaker", "Our team", "A clear communicator", "The presenter",
            "My colleague", "The negotiator", "A skilled listener", "The mediator",
            "Our whole class", "A public speaker",
            "The debate team", "My mentor", "A confident student",
            "The interpreter", "The keynote speaker",
        ],
        "verbs_b": ["said", "asked", "listened", "replied", "nodded", "explained", "agreed", "wrote"],
        "verbs_i": ["conveyed", "persuaded", "clarified", "summarised", "facilitated", "negotiated", "moderated"],
        "verbs_a": [
            "rhetorically structured an argument that",
            "diplomatically reframed the conversation around",
            "deployed active listening strategies to facilitate",
            "synthesised competing narratives to arrive at",
        ],
        "objects_b": [
            "the message clearly", "a simple idea", "the instructions",
            "an important question", "a quick thank you", "a kind word",
        ],
        "objects_i": [
            "the project update", "a difficult piece of feedback",
            "the team's concerns", "a clear action plan",
            "the key findings of the research",
        ],
        "objects_a": [
            "the underlying interests of all stakeholders in the dispute",
            "a nuanced argument accessible to both specialist and lay audiences",
            "a persuasive narrative grounded in both data and human experience",
        ],
        "extras_b": [
            "in simple words.", "with a smile.", "very politely.",
            "without any confusion.", "in front of the class.",
        ],
        "extras_i": [
            "in a professional and respectful tone.",
            "using concrete examples and analogies.",
            "adapting the message to the audience.",
        ],
        "extras_a": [
            "leveraging rhetorical appeals of ethos, pathos, and logos.",
            "in alignment with culturally sensitive communication norms.",
            "while navigating significant power imbalances between parties.",
        ],
        "questions_b": [
            "Did you understand what I just said?",
            "Can you say that again, please?",
            "How do I say this in a nicer way?",
            "Can you speak a little slower?",
            "Should I send an email or call?",
        ],
        "questions_i": [
            "How do you give feedback without upsetting someone?",
            "What makes a presentation truly engaging?",
            "How do you handle a difficult conversation at work?",
            "What is the difference between assertive and aggressive communication?",
        ],
        "questions_a": [
            "How do power dynamics shape the structure and content of organisational communication?",
            "What does Gricean pragmatics tell us about the cooperative principles underlying conversation?",
            "How does code-switching function as both an adaptive strategy and a marker of identity?",
        ],
    },

    # ── 12 NEW DOMAINS ────────────────────────────────────────────────────────

    "finance": {
        "subjects": [
            "The investor", "Our finance team", "The bank", "A financial adviser",
            "The central bank", "The market analyst", "A hedge fund manager",
            "The startup founder", "Our accountant", "The insurance provider",
            "A young saver", "The pension fund", "The regulator",
        ],
        "verbs_b": ["saved", "spent", "earned", "paid", "borrowed", "checked", "deposited", "invested"],
        "verbs_i": ["allocated", "diversified", "budgeted", "forecasted", "audited", "reported", "structured"],
        "verbs_a": [
            "stress-tested", "modelled the risk exposure of",
            "optimised the capital allocation for",
            "systematically evaluated the yield curve implications of",
            "quantitatively analysed the volatility of",
        ],
        "objects_b": [
            "a small amount each month", "the household bills",
            "a new bank account", "the weekly budget", "a receipt",
        ],
        "objects_i": [
            "the annual tax return", "a diversified investment portfolio",
            "the company's cash flow", "a long-term savings plan",
            "the quarterly financial statements",
        ],
        "objects_a": [
            "the macroeconomic exposure of the portfolio to sovereign risk",
            "the Basel III capital adequacy requirements",
            "the systemic liquidity risks in the interbank lending market",
        ],
        "extras_b": [
            "every month.", "without going over budget.", "on time.",
            "with the help of an app.", "before the deadline.",
        ],
        "extras_i": [
            "using a conservative asset allocation strategy.",
            "ahead of the regulatory reporting deadline.",
            "following the internal audit recommendations.",
        ],
        "extras_a": [
            "under a scenario of sustained interest rate compression.",
            "drawing on Monte Carlo simulation frameworks.",
            "in compliance with IFRS 9 impairment provisioning standards.",
        ],
        "questions_b": [
            "How much does this cost?",
            "Should I open a savings account?",
            "Is it better to pay by card or cash?",
            "How do I set a monthly budget?",
            "What is interest?",
        ],
        "questions_i": [
            "What is the difference between a stock and a bond?",
            "How does compound interest work over time?",
            "What is an index fund and why is it popular?",
            "How much should I be saving for retirement?",
            "What is the best way to pay off debt quickly?",
        ],
        "questions_a": [
            "How does monetary policy transmission affect credit supply in emerging market economies?",
            "What are the systemic implications of central bank digital currencies for commercial banking?",
            "How do behavioural finance insights challenge the efficient market hypothesis?",
        ],
    },

    "law": {
        "subjects": [
            "The lawyer", "The judge", "A legal aid solicitor", "The jury",
            "The defendant", "A rights organisation", "The prosecutor",
            "The legal team", "A paralegal", "The magistrate",
            "A law student", "The barrister", "The public defender",
        ],
        "verbs_b": ["argued", "ruled", "asked", "said", "signed", "reviewed", "agreed", "filed"],
        "verbs_i": ["submitted", "cross-examined", "appealed", "advised", "prosecuted", "acquitted", "challenged"],
        "verbs_a": [
            "applied the proportionality test to",
            "constructed a constitutional challenge against",
            "engaged in statutory interpretation of",
            "submitted expert testimony regarding",
        ],
        "objects_b": [
            "the contract", "the form", "the claim", "a document",
            "the statement", "the case",
        ],
        "objects_i": [
            "the appeal", "the evidence", "the court filing",
            "the settlement agreement", "the legal precedent",
            "the witness testimony",
        ],
        "objects_a": [
            "the proportionality of the legislative measure under scrutiny",
            "the implied right to privacy under the constitutional framework",
            "the extraterritorial application of domestic data protection law",
        ],
        "extras_b": [
            "in writing.", "before the deadline.", "at the local court.",
            "without any legal help.", "by the end of the week.",
        ],
        "extras_i": [
            "following standard legal procedure.",
            "before the case went to trial.",
            "after extensive consultation with the client.",
        ],
        "extras_a": [
            "in light of recent Supreme Court jurisprudence.",
            "applying a purposive approach to statutory interpretation.",
            "drawing on comparative constitutional law from three jurisdictions.",
        ],
        "questions_b": [
            "Do I need a lawyer for this?",
            "What does this contract mean?",
            "Is that actually against the law?",
            "How long will this take?",
            "What happens if I miss the deadline?",
        ],
        "questions_i": [
            "What is the difference between civil and criminal law?",
            "How does small claims court work?",
            "Can I appeal this decision?",
            "What rights do I have if I am stopped by police?",
            "What is the role of a solicitor versus a barrister?",
        ],
        "questions_a": [
            "How does the doctrine of precedent function differently across common law and civil law systems?",
            "What are the constitutional limits on parliamentary sovereignty in a dualist legal system?",
            "How should courts balance free expression against the right to reputation in defamation cases?",
        ],
    },

    "sport": {
        "subjects": [
            "The athlete", "The team", "Our coach", "The referee",
            "A sports journalist", "The captain", "The rookie",
            "The physio", "Our local club", "The national squad",
            "The sports analyst", "A record-breaking sprinter",
            "The tournament director", "A young fan",
        ],
        "verbs_b": ["won", "lost", "scored", "trained", "played", "ran", "jumped", "competed"],
        "verbs_i": ["qualified", "dominated", "recovered", "strategised", "defended", "challenged", "sprinted"],
        "verbs_a": [
            "periodised the training load of",
            "biomechanically optimised the performance of",
            "statistically modelled the injury risk for",
            "tactically dismantled the defensive structure of",
        ],
        "objects_b": [
            "the match", "the race", "the game", "the tournament",
            "a goal", "a personal best", "the first round",
        ],
        "objects_i": [
            "the championship final", "the regional qualifier",
            "the training programme", "the squad's fitness data",
            "the tactical formation", "the pre-season schedule",
        ],
        "objects_a": [
            "the evidence base for altitude training in endurance athletes",
            "the long-term athlete development framework",
            "the biomechanical determinants of sprint performance",
        ],
        "extras_b": [
            "in the final minutes.", "with great determination.",
            "in front of a huge crowd.", "against a strong opponent.",
            "for the first time this season.",
        ],
        "extras_i": [
            "after months of intensive preparation.", "despite a difficult injury period.",
            "with a carefully planned race strategy.", "against the pre-tournament favourites.",
        ],
        "extras_a": [
            "using GPS tracking and heart rate variability data.",
            "within a periodised annual training plan.",
            "drawing on sports psychology and cognitive performance research.",
        ],
        "questions_b": [
            "Did we win?",
            "What is the score?",
            "When is the next match?",
            "Who scored the goal?",
            "Is the game on tonight?",
        ],
        "questions_i": [
            "How do professional athletes recover so quickly from injury?",
            "What makes a good sports team beyond individual talent?",
            "How does altitude training improve endurance performance?",
            "What is the role of a sports psychologist?",
        ],
        "questions_a": [
            "How does the commercialisation of elite sport affect grassroots participation?",
            "What are the ethical implications of genetic screening in athlete selection?",
            "How do tactical analytics reshape coaching decisions at the elite level?",
        ],
    },

    "music": {
        "subjects": [
            "The musician", "Our band", "The composer", "A solo artist",
            "The producer", "The sound engineer", "My favourite singer",
            "The orchestra", "A busker", "The recording studio",
            "The music teacher", "A session musician", "The choir",
            "The DJ", "An up-and-coming songwriter",
        ],
        "verbs_b": ["played", "sang", "listened", "practised", "performed", "recorded", "hummed", "wrote"],
        "verbs_i": ["composed", "produced", "arranged", "collaborated", "rehearsed", "mixed", "released"],
        "verbs_a": [
            "orchestrated a thematic development within",
            "deconstructed the harmonic language of",
            "reimagined the canonical form of",
            "contextualised the cultural significance of",
        ],
        "objects_b": [
            "a simple melody", "a favourite song", "the chorus",
            "a short piece", "the rhythm", "a few chords",
        ],
        "objects_i": [
            "a new album", "a live performance", "an original composition",
            "a studio recording session", "an acoustic cover",
            "a collaborative EP",
        ],
        "objects_a": [
            "the polyrhythmic structure underpinning the arrangement",
            "the socio-political subtext embedded in the lyrics",
            "the timbral evolution across the composer's late period works",
        ],
        "extras_b": [
            "every evening.", "during the school concert.", "for fun.",
            "with great passion.", "in front of friends.",
        ],
        "extras_i": [
            "to a captivated live audience.", "after months of rehearsal.",
            "with an emotionally resonant performance.", "across multiple genres.",
        ],
        "extras_a": [
            "within the tradition of late Romantic harmonic practice.",
            "drawing on ethnomusicological field recordings.",
            "through a cross-genre synthesis of electronic and acoustic elements.",
        ],
        "questions_b": [
            "What is your favourite song at the moment?",
            "Do you play any instruments?",
            "Is that music loud enough?",
            "Can you teach me that tune?",
            "Who is your favourite artist?",
        ],
        "questions_i": [
            "How does music affect mood and concentration?",
            "What is the difference between a major and minor key?",
            "How do musicians memorise long pieces?",
            "What does a music producer actually do?",
        ],
        "questions_a": [
            "How does tonality function as a carrier of cultural meaning across different musical traditions?",
            "What is the relationship between metric ambiguity and emotional tension in Western art music?",
            "How has digital streaming reshaped the economics of music production and distribution?",
        ],
    },

    "education_policy": {
        "subjects": [
            "The education minister", "Teachers across the country", "Parents",
            "The curriculum committee", "School governors", "Independent inspectors",
            "University admissions teams", "Student unions", "Policy researchers",
            "The national teaching authority", "Education reform advocates",
        ],
        "verbs_b": ["changed", "asked", "agreed", "helped", "started", "decided", "approved", "reviewed"],
        "verbs_i": ["consulted", "reformed", "implemented", "evaluated", "recommended", "piloted", "proposed"],
        "verbs_a": [
            "conducted a systematic review of",
            "developed an evidence-based framework for",
            "critically assessed the equity implications of",
            "operationalised a theory of change around",
        ],
        "objects_b": [
            "the school day", "the exam timetable", "the reading programme",
            "the new curriculum", "the lunch menu",
        ],
        "objects_i": [
            "the national assessment framework", "the teacher training pathway",
            "the inspection regime", "the funding allocation model",
            "the special educational needs provision",
        ],
        "objects_a": [
            "the socioeconomic determinants of educational attainment gaps",
            "the long-term impact of early years investment on life outcomes",
            "the relationship between school autonomy and pupil achievement",
        ],
        "extras_b": [
            "before the new term.", "with the school's support.", "last year.",
            "in primary schools.", "for younger pupils.",
        ],
        "extras_i": [
            "following extensive consultation with stakeholders.",
            "in response to declining literacy rates.",
            "across disadvantaged school communities.",
        ],
        "extras_a": [
            "drawing on longitudinal cohort data from three national studies.",
            "within the context of international PISA benchmarking.",
            "to address persistent attainment gaps along socioeconomic lines.",
        ],
        "questions_b": [
            "What will school be like next year?",
            "Are they changing the exams?",
            "Will this affect my child's school?",
            "What does the new curriculum include?",
        ],
        "questions_i": [
            "How are schools assessed for quality?",
            "What changes are being made to teacher training?",
            "How does funding affect school performance?",
            "What support is available for pupils with learning difficulties?",
        ],
        "questions_a": [
            "To what extent does school accountability policy improve educational outcomes or simply redistribute disadvantage?",
            "How does the evidence compare between phonics-first and whole-language reading instruction approaches?",
            "What structural reforms most effectively close attainment gaps in highly unequal education systems?",
        ],
    },

    "mental_health": {
        "subjects": [
            "The therapist", "My counsellor", "A mental health nurse",
            "The support group", "A researcher in psychology", "My friend",
            "The psychiatrist", "Young people across the country",
            "The peer support volunteer", "A clinical psychologist",
            "The mental health charity", "A patient advocate",
        ],
        "verbs_b": ["talked", "felt", "helped", "listened", "shared", "attended", "rested", "asked"],
        "verbs_i": ["supported", "reflected", "opened up about", "recovered from", "managed", "explored", "disclosed"],
        "verbs_a": [
            "developed a trauma-informed approach to",
            "empirically validated a therapeutic model for",
            "systematically addressed the biopsychosocial dimensions of",
            "evaluated the efficacy of mindfulness-based interventions for",
        ],
        "objects_b": [
            "their feelings", "a difficult week", "the session",
            "some worrying thoughts", "the appointment",
        ],
        "objects_i": [
            "anxiety and low mood", "a period of burnout",
            "the therapeutic relationship", "coping strategies for stress",
            "the impact of sleep on mental health",
        ],
        "objects_a": [
            "the neurobiological mechanisms underlying treatment-resistant depression",
            "the efficacy of schema therapy versus CBT in personality disorder treatment",
            "the role of social determinants in shaping mental health outcomes at population level",
        ],
        "extras_b": [
            "with a trusted person.", "after a rest.", "at their own pace.",
            "in a safe environment.", "with professional help.",
        ],
        "extras_i": [
            "after months of working through the underlying issues.",
            "using evidence-based cognitive behavioural techniques.",
            "within a structured outpatient support programme.",
        ],
        "extras_a": [
            "drawing on the latest NICE clinical guidelines for psychological therapies.",
            "within a stepped-care model of service delivery.",
            "incorporating lived experience perspectives into the research design.",
        ],
        "questions_b": [
            "Are you doing okay?",
            "Do you want to talk about it?",
            "Is it okay to feel this way?",
            "Should I see someone about this?",
        ],
        "questions_i": [
            "What is the difference between anxiety and an anxiety disorder?",
            "How do I find a good therapist?",
            "What are the signs of burnout?",
            "How can I support someone who is struggling?",
        ],
        "questions_a": [
            "How does early childhood adversity shape the developing stress response system?",
            "What are the comparative outcomes of pharmacological versus psychotherapeutic interventions for major depression?",
            "How should mental health services be configured to address population-level demand sustainably?",
        ],
    },

    "architecture": {
        "subjects": [
            "The architect", "The design team", "Urban planners",
            "The building committee", "A structural engineer", "The contractor",
            "A heritage conservation officer", "The interior designer",
            "Local residents", "The city council", "A landscape architect",
        ],
        "verbs_b": ["built", "designed", "drew", "measured", "planned", "visited", "approved", "opened"],
        "verbs_i": ["renovated", "consulted", "drafted", "assessed", "developed", "presented", "surveyed"],
        "verbs_a": [
            "applied passive solar design principles to",
            "critically appraised the structural integrity of",
            "developed a contextually sensitive master plan for",
            "integrated biophilic design elements throughout",
        ],
        "objects_b": [
            "a new house", "the bridge", "the school building",
            "the community centre", "a small extension",
        ],
        "objects_i": [
            "the mixed-use development", "the sustainable office block",
            "the historic restoration project", "the public square",
            "a modular housing scheme",
        ],
        "objects_a": [
            "the urban regeneration masterplan for the post-industrial waterfront site",
            "the net-zero carbon retrofit of the Grade II listed building",
            "the socially inclusive design framework for the high-density housing development",
        ],
        "extras_b": [
            "in the city centre.", "last spring.", "for the community.",
            "on a tight budget.", "in just six months.",
        ],
        "extras_i": [
            "following extensive community consultation.", "within a strict conservation brief.",
            "with an emphasis on natural light and ventilation.",
            "using reclaimed and sustainable materials.",
        ],
        "extras_a": [
            "meeting BREEAM Outstanding certification criteria.",
            "through an integrated design process involving all disciplines from the outset.",
            "drawing on post-occupancy evaluation data from comparable schemes.",
        ],
        "questions_b": [
            "Who designed that building?",
            "How tall is it?",
            "When was it built?",
            "Can we go inside?",
            "Will they be building there?",
        ],
        "questions_i": [
            "What is the difference between a load-bearing and a curtain wall?",
            "How do architects design for natural light?",
            "What makes a building energy efficient?",
            "How are planning permissions granted?",
        ],
        "questions_a": [
            "How should the tension between heritage preservation and urban densification be resolved in historic city centres?",
            "What design principles most effectively support community cohesion in high-density residential environments?",
            "How does the choice of material affect a building's whole-life carbon footprint?",
        ],
    },

    "transport": {
        "subjects": [
            "The commuter", "The bus driver", "Transport planners",
            "The rail network", "Cyclists", "The airport authority",
            "Pedestrians", "The logistics company", "A road safety campaigner",
            "Local residents", "The delivery driver", "The fleet manager",
        ],
        "verbs_b": ["caught", "missed", "waited", "drove", "cycled", "walked", "boarded", "arrived"],
        "verbs_i": ["navigated", "commuted", "rerouted", "scheduled", "maintained", "operated", "tracked"],
        "verbs_a": [
            "modelled the modal shift implications of",
            "evaluated the decarbonisation pathway for",
            "integrated multimodal connectivity into",
            "optimised the network capacity of",
        ],
        "objects_b": [
            "the bus", "the train", "a taxi", "the underground",
            "the morning commute", "a bus pass",
        ],
        "objects_i": [
            "the rail timetable", "the cycle infrastructure plan",
            "the congestion data", "the public transport network",
            "the freight logistics schedule",
        ],
        "objects_a": [
            "the carbon impact of last-mile delivery operations",
            "the equity implications of urban transport investment decisions",
            "the demand modelling for a new mass rapid transit corridor",
        ],
        "extras_b": [
            "on time.", "in heavy traffic.", "at the last minute.",
            "during rush hour.", "without a ticket.",
        ],
        "extras_i": [
            "following a service disruption.", "despite engineering works.",
            "using real-time journey planning apps.", "across three different modes.",
        ],
        "extras_a": [
            "in line with the net-zero transport strategy.",
            "drawing on agent-based transport demand models.",
            "within the constraints of an aging infrastructure estate.",
        ],
        "questions_b": [
            "Which bus goes to the town centre?",
            "Is the train on time?",
            "How much is a return ticket?",
            "Where is the nearest bus stop?",
            "How long does the journey take?",
        ],
        "questions_i": [
            "How do cities reduce traffic congestion effectively?",
            "What is the environmental case for electric vehicles?",
            "How does public transport investment affect property values?",
            "What are the benefits of congestion charging?",
        ],
        "questions_a": [
            "How should transport planners balance the competing demands of car users, cyclists, and pedestrians in urban cores?",
            "What role does land use planning play in reducing the need to travel?",
            "How can autonomous vehicle deployment be governed to maximise safety and equity?",
        ],
    },

    "history": {
        "subjects": [
            "Historians", "The archive", "Archaeologists", "A biographer",
            "The research team", "An oral history project", "The museum curator",
            "Ancient chroniclers", "A documentary filmmaker",
            "A social historian", "The primary source",
            "The revisionist historian", "A local history society",
        ],
        "verbs_b": ["found", "discovered", "recorded", "wrote", "studied", "described", "noted", "showed"],
        "verbs_i": ["documented", "excavated", "reinterpreted", "examined", "catalogued", "reconstructed", "analysed"],
        "verbs_a": [
            "critically reassessed the dominant historiography of",
            "applied a postcolonial lens to",
            "interrogated the archival silences surrounding",
            "triangulated oral testimonies with documentary evidence about",
        ],
        "objects_b": [
            "the old photograph", "a historical record", "an ancient coin",
            "the local archive", "a handwritten letter",
        ],
        "objects_i": [
            "the political causes of the conflict", "the role of ordinary people",
            "the economic conditions of the period",
            "the cultural exchange between civilisations",
            "a previously unknown settlement",
        ],
        "objects_a": [
            "the gendered dimensions of wartime labour mobilisation",
            "the ideological construction of national identity in nineteenth-century Europe",
            "the agency of colonised populations within asymmetric power structures",
        ],
        "extras_b": [
            "hundreds of years ago.", "for the first time.", "in a museum.",
            "with great detail.", "using old records.",
        ],
        "extras_i": [
            "after decades of historical neglect.", "using newly declassified documents.",
            "challenging long-standing assumptions about the period.",
        ],
        "extras_a": [
            "drawing on subaltern studies and social history methodology.",
            "synthesising archaeological, textual, and material culture evidence.",
            "within the framework of comparative global history.",
        ],
        "questions_b": [
            "What happened a long time ago?",
            "Who built this?",
            "How old is this?",
            "Did people live here before us?",
            "What was it like back then?",
        ],
        "questions_i": [
            "What caused the First World War?",
            "How did the Industrial Revolution change daily life?",
            "What is the significance of the Silk Road?",
            "How did colonialism shape the modern world?",
        ],
        "questions_a": [
            "To what extent do nationalist historiographies distort our understanding of contested historical events?",
            "How should historians handle the silences and biases inherent in colonial archive production?",
            "What methodological challenges arise when conducting oral history research in communities that experienced collective trauma?",
        ],
    },

    "arts": {
        "subjects": [
            "The painter", "Our local gallery", "A sculptor", "The theatre company",
            "A film director", "The dance troupe", "A graphic novelist",
            "The community arts project", "A ceramicist",
            "The arts council", "A printmaker", "The exhibition curator",
            "A street artist", "The emerging talent",
        ],
        "verbs_b": ["painted", "drew", "performed", "created", "exhibited", "showed", "sketched", "sculpted"],
        "verbs_i": ["curated", "collaborated", "interpreted", "staged", "commissioned", "experimented with", "explored"],
        "verbs_a": [
            "deconstructed the aesthetic conventions of",
            "situated the work within a broader cultural critique of",
            "interrogated the representational politics of",
            "developed a practice-led research methodology around",
        ],
        "objects_b": [
            "a portrait", "a landscape", "a short play",
            "a ceramic bowl", "a pencil sketch",
        ],
        "objects_i": [
            "a series of mixed-media works", "a community mural",
            "a site-specific installation", "a touring theatre production",
            "an illustrated graphic memoir",
        ],
        "objects_a": [
            "the dialectic between form and content in contemporary sculpture",
            "the ethics of cultural appropriation in collaborative cross-cultural artistic practice",
            "the tension between institutional legitimacy and radical artistic intent",
        ],
        "extras_b": [
            "for the school art competition.", "during the summer festival.",
            "with bold use of colour.", "in a local gallery.", "from imagination.",
        ],
        "extras_i": [
            "in response to the social conditions around them.",
            "drawing on personal memory and family history.",
            "using unconventional materials and processes.",
        ],
        "extras_a": [
            "engaging critically with the canon of Western art history.",
            "through a participatory methodology involving community co-creators.",
            "in dialogue with concurrent developments in philosophy and critical theory.",
        ],
        "questions_b": [
            "Did you make that yourself?",
            "What does this painting mean?",
            "How long did this take?",
            "Can I try painting too?",
            "What inspired you to make this?",
        ],
        "questions_i": [
            "How do artists develop their own style?",
            "What is the role of the arts in society?",
            "How has digital technology changed artistic practice?",
            "What makes public art successful?",
        ],
        "questions_a": [
            "How does institutional power shape which art is seen, valued, and preserved?",
            "What is the relationship between aesthetic autonomy and social commitment in contemporary artistic practice?",
            "How do participatory art practices challenge traditional distinctions between artist and audience?",
        ],
    },
}

# ════════════════════════════════════════════════════════════════════════════
# STANDALONE SENTENCE POOLS  (greatly expanded)
# ════════════════════════════════════════════════════════════════════════════

STANDALONE_BEGINNER: list[str] = [
    "The sun rises in the east every morning.",
    "She always drinks a glass of water before breakfast.",
    "He loves playing football with his friends.",
    "The cat sat quietly on the mat.",
    "We go to school five days a week.",
    "My mum cooks dinner every evening.",
    "The baby laughed at the funny toy.",
    "It was a bright and sunny day.",
    "He forgot to bring his umbrella.",
    "She smiled and said good morning.",
    "The little boy ran to the playground.",
    "They finished their lunch before the bell rang.",
    "Dad helped me fix my bicycle yesterday.",
    "The dog wagged its tail happily.",
    "I like reading books before going to sleep.",
    "She wrote her name on the board.",
    "It gets dark early in winter.",
    "We cleaned the classroom together.",
    "The flowers in the garden are beautiful.",
    "He tied his shoelaces all by himself.",
    "We had pancakes for breakfast this morning.",
    "The lunchbox was full of colourful fruit.",
    "She packed her bag the night before school.",
    "The bus arrived five minutes early.",
    "He waved goodbye to his mum at the school gate.",
    "The playground was full of children at break time.",
    "She borrowed a book from the library.",
    "We sat together and ate our snacks.",
    "The shop was closed when we arrived.",
    "He put on his jacket before going outside.",
    "The birds sing loudly in the morning.",
    "Rain is falling gently on the window.",
    "The soup is warm and delicious.",
    "She draws a picture every afternoon.",
    "He helps his mum carry the shopping bags.",
    "We say please and thank you every day.",
    "The library is quiet and peaceful.",
    "She learned a new word today.",
    "He shared his biscuits with his friend.",
    "The classroom has twenty-four chairs.",
    "She painted a picture of her house.",
    "He ran all the way home from school.",
    "The kitten slept in a small basket.",
    "She asked her teacher a question.",
    "The park was busy on Saturday morning.",
    "He found a shiny stone on the path.",
    "The bread smelled wonderful when it came out of the oven.",
    "She counted all the way to one hundred.",
    "He helped his friend carry the heavy box.",
    "The classroom window was wide open all morning.",
]

STANDALONE_INTERMEDIATE: list[str] = [
    "Learning a new language opens many opportunities.",
    "She organised her notes carefully before the exam.",
    "The team worked together to solve the problem.",
    "Regular exercise has many long-term health benefits.",
    "He apologised sincerely after the misunderstanding.",
    "The documentary highlighted the effects of pollution on oceans.",
    "She struggled at first but eventually mastered the skill.",
    "They decided to take a different approach to the project.",
    "The new policy aims to reduce food waste in schools.",
    "He stayed up late to finish the research paper.",
    "Understanding different cultures helps reduce prejudice.",
    "The company introduced a flexible working schedule.",
    "She asked a thoughtful question during the lecture.",
    "They discovered that collaboration improved their results.",
    "The bridge was closed for safety reasons.",
    "He kept a daily journal to track his progress.",
    "The meeting was more productive than expected.",
    "She carefully reviewed every line of her code.",
    "The children raised money for a local charity.",
    "He explained the concept clearly and patiently.",
    "Volunteering in your community builds a sense of purpose.",
    "Saving even a small amount each month adds up over time.",
    "She realised that preparation makes a big difference.",
    "Feedback is most useful when it is specific and kind.",
    "He found that breaking tasks into steps made them easier.",
    "Public libraries are valuable resources for everyone.",
    "A good night's sleep improves focus the next day.",
    "She practised her speech in front of the mirror.",
    "Reading widely exposes you to different ways of thinking.",
    "They set clear goals and reviewed their progress weekly.",
    "Travelling broadens your perspective in unexpected ways.",
    "She tried the local food and found it wonderful.",
    "He learned a few phrases in the local language before his trip.",
    "The museum had exhibits from over fifty countries.",
    "They stayed in a small guesthouse near the town centre.",
    "Different communities have different ways of celebrating.",
    "She brought back handmade gifts for everyone at home.",
    "He was surprised by how welcoming the locals were.",
    "The train journey offered spectacular views of the countryside.",
    "Understanding local customs is a sign of respect.",
    "She set aside time each week to learn something new.",
    "He noticed that small habits compound into big changes.",
    "The workshop brought together people from very different backgrounds.",
    "She realised the value of asking for help sooner.",
    "Clear communication prevents most misunderstandings before they start.",
    "He adapted quickly once he understood the expectations.",
    "The project ran over time but delivered something genuinely useful.",
    "She found that consistency mattered more than motivation.",
    "He made a point of listening before offering a response.",
    "The feedback they received turned out to be exactly what they needed.",
]

STANDALONE_ADVANCED: list[str] = [
    "The proliferation of misinformation on digital platforms undermines public discourse.",
    "Cognitive biases often operate below the threshold of conscious awareness.",
    "The researcher's findings challenge several long-standing assumptions in the field.",
    "Structural inequalities are reproduced through seemingly neutral institutional practices.",
    "The interplay between syntax and semantics remains a central debate in linguistics.",
    "Advancements in quantum computing may render current encryption protocols obsolete.",
    "The narrative's unreliable narrator serves as a critique of subjective perception.",
    "Regulatory frameworks have struggled to keep pace with technological innovation.",
    "Effective risk communication requires balancing scientific accuracy with public accessibility.",
    "The study employed a mixed-methods approach to triangulate the qualitative findings.",
    "Post-colonial theory reconceptualises the power dynamics embedded in knowledge production.",
    "Environmental degradation and social inequality are deeply interrelated phenomena.",
    "The algorithm's opaque decision-making process raises significant accountability concerns.",
    "A nuanced reading of the text reveals layers of intertextual reference.",
    "The philosopher argued that free will and determinism are not mutually exclusive.",
    "Institutional trust is rebuilt through consistent, transparent, and accountable governance.",
    "The data reveals a statistically significant correlation, though causality remains unproven.",
    "Critical pedagogy encourages learners to interrogate the assumptions embedded in curricula.",
    "The legislation introduced safeguards against the misuse of biometric data.",
    "Interdisciplinary research often generates insights that siloed approaches cannot produce.",
    "Questions of justice cannot be disentangled from questions of power.",
    "The relationship between individual agency and social structure is one of sociology's central tensions.",
    "Technological determinism underestimates the role of human choice in shaping innovation trajectories.",
    "A robust democracy requires not just free elections but informed and engaged citizens.",
    "The distinction between descriptive and normative claims is essential in ethical reasoning.",
    "Cultural hegemony operates most effectively when it is least visible.",
    "Epistemic humility is the recognition of the limits of knowledge.",
    "The commodification of attention has reshaped what counts as meaningful communication.",
    "Language does not merely describe reality; it actively constructs it.",
    "Resilience is a dynamic capacity shaped by context and community.",
    "The tension between efficiency and equity runs through nearly every policy debate.",
    "Complexity science challenges the assumption that systems can be understood by reducing them to their parts.",
    "The burden of proof is not symmetrically distributed between those who assert and those who doubt.",
    "Soft power operates most effectively when it is not recognised as power at all.",
    "The concept of identity resists reduction to any single fixed category.",
    "Transparency in governance is necessary but not sufficient for accountability.",
    "The ethics of care challenge the primacy of abstract principle in moral reasoning.",
    "Populism exploits the gap between the legitimacy of institutions and the trust people place in them.",
    "The financialisation of everyday life has altered the temporal horizons of decision-making.",
    "Intersectionality reveals how systems of oppression reinforce and amplify each other.",
]

STANDALONE_SOCIAL_MEDIA: list[str] = [
    "Just got back from the most amazing trip of my life.",
    "That moment when everything finally comes together.",
    "Cannot believe how quickly this year has gone.",
    "Sharing this because it genuinely changed how I think.",
    "Small wins deserve to be celebrated too.",
    "Grateful for every single person who has supported this journey.",
    "Some days are harder than others, and that is completely fine.",
    "Reminder: progress, not perfection.",
    "Today was a good day and I just wanted to share that.",
    "This is what I have been working on for the past six months.",
    "Shoutout to everyone showing up every day even when it is tough.",
    "Not sure who needs to hear this but you are doing great.",
    "Sometimes the best moments are the ones you did not plan.",
    "Really proud of how far this community has come.",
    "Three things I learned this week that surprised me.",
    "It is okay to change your mind when you learn something new.",
    "Working on something exciting and I cannot wait to share it.",
    "A huge thank you to everyone who reached out this week.",
    "Back to basics and it feels really good.",
    "Quality always beats quantity in the long run.",
    "This week taught me to slow down and appreciate the small things.",
    "Building something meaningful takes time and that is worth remembering.",
    "Every single step forward counts, no matter how small.",
    "Something I wish I had known sooner — consistency beats intensity.",
    "Proud of this one. It took a lot longer than expected.",
    "Sharing this because someone out there might need it today.",
    "Learning something new every week is one of the best habits I have.",
    "The journey is genuinely more interesting than the destination.",
    "Started small, stayed consistent, and the results speak for themselves.",
    "There is always something to be grateful for if you look closely enough.",
    "The one thing nobody tells you about starting something new: it gets uncomfortable before it gets good.",
    "Three years ago I had no idea this would become part of my life.",
    "One conversation changed the direction I was heading in.",
    "Taking a break was the most productive thing I did this month.",
    "Not every day will look like progress, but most days are.",
    "Thank you to everyone who believed in this before there was anything to show.",
    "The thing about doing hard things is that they stop being as hard.",
    "Documenting this so future me remembers what this stage felt like.",
    "Done is better than perfect — but only just.",
    "It is wild how much can change in twelve months.",
]

STANDALONE_CUSTOMER_SUPPORT: list[str] = [
    "Thank you for reaching out to us today.",
    "I completely understand your frustration and I am here to help.",
    "Let me look into this for you right away.",
    "I have checked your account and I can see the issue.",
    "I apologise for any inconvenience this may have caused.",
    "We have escalated this to our technical team for immediate review.",
    "You should receive a confirmation email within the next few minutes.",
    "Your refund has been processed and may take three to five business days.",
    "I will make a note on your account so our team is aware.",
    "Is there anything else I can help you with today?",
    "We really value your feedback and it helps us improve.",
    "I am happy to walk you through the steps if that would help.",
    "Our team is working on resolving this as quickly as possible.",
    "Thank you for your patience while we look into this.",
    "I have sent a reset link to the email address on your account.",
    "Your order is currently in transit and should arrive by Thursday.",
    "I will personally ensure this is followed up before end of day.",
    "We appreciate your loyalty and want to make this right for you.",
    "Let me transfer you to a specialist who can assist further.",
    "I have applied a courtesy credit to your account.",
    "Could you provide your order number so I can look this up?",
    "I can see the order was dispatched yesterday evening.",
    "We are sorry for the wait and appreciate your continued patience.",
    "Your feedback has been passed to the relevant team for review.",
    "We would love to make this experience better for you.",
    "I can confirm that your case has been assigned to a senior adviser.",
    "To protect your account, I will need to verify a few details first.",
    "We have flagged this as a priority and you will hear back within two hours.",
    "I have cancelled the duplicate charge and you should see the credit shortly.",
    "Thank you for bringing this to our attention — this helps us improve.",
    "I will stay on the line until we have fully resolved this for you.",
    "Your replacement item has been dispatched and is on its way.",
    "I have extended your subscription by one month as a goodwill gesture.",
    "The issue has now been resolved at our end and everything should work normally.",
    "We take reports like this very seriously and will investigate thoroughly.",
]

STANDALONE_CHILD_FRIENDLY: list[str] = [
    "The big red bus drives down the busy street.",
    "She found a shiny coin on the way to school.",
    "He drew a picture of his favourite animal.",
    "The puppy ran around the garden all afternoon.",
    "We counted the stars before going to bed.",
    "She built a tall tower with her colourful blocks.",
    "He learned how to ride his bike without help.",
    "The class planted seeds and watched them grow.",
    "She made a card for her teacher's birthday.",
    "He helped set the table before dinner.",
    "The butterfly landed gently on the flower.",
    "We played in the leaves and had so much fun.",
    "She read her favourite book three times this week.",
    "He fed the ducks at the pond with his dad.",
    "The rain made lovely puddles to jump in.",
    "She drew a rainbow with all her crayons.",
    "He shared his lunch with a friend who forgot theirs.",
    "We listened to a story and drew pictures about it.",
    "The kitten purred softly when she stroked it.",
    "He was very kind to the new boy at school.",
    "The frog jumped from one lily pad to the next.",
    "She counted ten apples in the basket.",
    "He waved hello to the friendly shopkeeper.",
    "The leaves turned orange and red in autumn.",
    "She helped her grandma water the plants.",
    "The little penguin waddled across the ice.",
    "He blew out all the candles on his birthday cake.",
    "The bunny hopped through the long green grass.",
    "She wore her favourite stripy socks to the party.",
    "He made a boat out of sticks and sent it down the stream.",
    "The snail moved slowly but always got where it was going.",
    "She made a den out of cushions and blankets.",
    "The snowflakes fell silently onto the garden.",
    "He grew a sunflower that was taller than the fence.",
    "The class made a book and everyone wrote one page.",
    "She learned how to whistle on a quiet afternoon.",
    "He lined up all his toy cars from biggest to smallest.",
    "The little owl blinked its big eyes in the moonlight.",
    "She carried the bucket very carefully all the way to the sandpit.",
    "He smiled when he saw his name written in gold stars.",
]

STANDALONE_INSTRUCTIONAL: list[str] = [
    "Please remember to save your work before closing the application.",
    "First, read the instructions carefully before you begin.",
    "Make sure to double-check your answers before submitting.",
    "Always wash your hands before handling food.",
    "To start the process, click the green button in the top-right corner.",
    "Begin by writing your name and the date at the top of the page.",
    "Do not forget to charge your device overnight.",
    "Press the power button and hold it for three seconds.",
    "Start with the easier questions and come back to the harder ones.",
    "Keep your workspace tidy to help you stay focused.",
    "Use bullet points to organise your main ideas clearly.",
    "Check the expiry date before using any medication.",
    "Follow the steps in order and do not skip any.",
    "If you are unsure, ask for help rather than guessing.",
    "Review your work once more before you hand it in.",
    "Label each section clearly so your reader can follow along.",
    "Allow the mixture to cool completely before moving to the next step.",
    "Ensure all participants have read the safety guidelines before starting.",
    "Update your password regularly and never share it with anyone.",
    "Keep a record of any changes you make for future reference.",
    "Before starting, gather all the materials you will need.",
    "Make sure the area is well-ventilated before beginning.",
    "Take a short break after every forty-five minutes of focused work.",
    "Double-check the spelling of names and dates before printing.",
    "Back up your files at the end of each working session.",
    "Always test on a small area first before applying widely.",
    "Read the full document before signing anything.",
    "Set a timer so you stay within the recommended duration.",
    "Communicate clearly with your team before making any changes.",
    "If the system asks you to restart, save everything first.",
    "Only proceed to the next step once the previous one is complete.",
    "Take photographs at each stage so you have a visual record.",
    "When in doubt, refer back to the original specification.",
    "Use the checklist to confirm each task before marking it complete.",
    "Keep all original packaging until you are sure the item works correctly.",
]

STANDALONE_STORYTELLING: list[str] = [
    "The door creaked open slowly, and nobody was sure what was on the other side.",
    "She had waited her whole life for a moment like this.",
    "He looked out at the horizon and made a decision that would change everything.",
    "Nobody had ever seen the town so quiet on a summer's evening.",
    "By the time they realised what was happening, it was already too late.",
    "She opened the letter with trembling hands.",
    "The journey began before sunrise, with only a map and a sense of curiosity.",
    "He had never expected to find the answer in such an ordinary place.",
    "The old house held more memories than any of them had bargained for.",
    "She told herself it was just nerves, but deep down she knew it was more than that.",
    "They had been walking for hours when the path finally opened into a clearing.",
    "The photograph on the table stopped him in his tracks.",
    "She smiled, but there was something in her eyes that told a different story.",
    "The moment the music started, everything else faded away.",
    "He had promised to be back by sunset, and the sky was already turning orange.",
    "There was a letter tucked beneath the front door when she arrived home.",
    "They had always assumed the forest held no surprises, until that afternoon.",
    "She stepped off the train into a city she had only ever dreamed about.",
    "For the first time in years, he allowed himself to hope.",
    "The silence that followed was louder than anything anyone had said.",
    "She had told the story so many times that it no longer felt like her own.",
    "He reached the top of the hill and finally understood why the climb had been worth it.",
    "The last page of the notebook was blank, and that felt like a beginning.",
    "None of them knew it at the time, but that afternoon would be the one they talked about for years.",
    "She put the key in the lock, took a breath, and opened the door.",
    "He had been carrying that secret for so long that setting it down felt strange.",
    "There was something in the way she said goodbye that made him turn back.",
    "The town looked completely different after everything that had happened.",
    "She did not know what she had been expecting, but it was not this.",
    "By morning, everything had changed, though nobody could say exactly when it had started.",
    "The note was short, unsigned, and left on a seat that should have been empty.",
    "He had the feeling that the story was only just beginning.",
    "They found what they were looking for in the last place any of them had thought to look.",
    "She stood at the edge of the decision for a long time before finally stepping through it.",
    "The others had gone ahead, but he stayed behind, just for a moment longer.",
]

STANDALONE_NEWS: list[str] = [
    "Local authorities have confirmed the project will be reviewed before the end of the month.",
    "A record number of participants registered for this year's event.",
    "Officials are calling for calm as discussions continue into the evening.",
    "The report found significant gaps in existing provision across multiple regions.",
    "A spokesperson said the organisation remains committed to a transparent process.",
    "New figures show the highest level of participation recorded in the past decade.",
    "Community leaders have welcomed the announcement but called for faster action.",
    "The decision came after months of consultation with those directly affected.",
    "Campaigners say the measures do not go far enough to address the underlying issues.",
    "A panel of independent experts will assess the evidence over the coming weeks.",
    "The statement confirmed that no final decision has yet been reached.",
    "Residents expressed concern about the pace of change in the local area.",
    "The initiative is expected to benefit thousands of people in the coming year.",
    "Officials have pledged to publish a full report within thirty days.",
    "Criticism mounted following revelations that key information had not been shared earlier.",
]

STANDALONE_PHILOSOPHY: list[str] = [
    "The question is not whether we are free, but what we do with the freedom we have.",
    "Ethics begins where rules run out.",
    "The examined life is not always easier, but it is harder to mislead.",
    "To understand something fully is to also understand its limits.",
    "A belief held without scrutiny is an assumption wearing borrowed clothes.",
    "Justice cannot be reduced to fairness alone, nor can fairness ignore justice.",
    "The distinction between knowing and understanding is one worth preserving.",
    "What we call common sense is often the sediment of forgotten arguments.",
    "Freedom is not the absence of constraint but the meaningful navigation of it.",
    "Some questions gain their value precisely because they resist easy answers.",
    "The purpose of argument is not always to win, but to clarify.",
    "To disagree well is a form of respect.",
    "The limits of language are, in some ways, the limits of what we can think.",
    "Doubt, applied carefully, is one of the most useful intellectual tools we have.",
    "Whether an action is good depends not only on what it produces but on what it is.",
]

STANDALONE_SCIENCE_FACTS: list[str] = [
    "The human brain contains approximately eighty-six billion neurons.",
    "Light from the sun takes around eight minutes to reach the Earth.",
    "Water expands when it freezes, which is why ice floats.",
    "DNA contains the instructions for building and running a living organism.",
    "The Earth's core is roughly as hot as the surface of the sun.",
    "Sound cannot travel through a vacuum because it requires a medium.",
    "A photon has no mass, which is why light can travel at its maximum speed.",
    "The cells in the human body collectively outnumber human cells ten to one.",
    "Carbon exists in forms as different as graphite and diamond.",
    "Every atom in your body was once part of a star.",
    "Bacteria were the first life forms on Earth and remain the most abundant.",
    "The universe is approximately thirteen point eight billion years old.",
    "Viruses are not considered alive because they cannot replicate independently.",
    "The human genome contains roughly three billion base pairs of DNA.",
    "Gravity is the weakest of the four fundamental forces but has infinite range.",
]

# ════════════════════════════════════════════════════════════════════════════
# DIALOGUE PAIRS  (600+)
# ════════════════════════════════════════════════════════════════════════════

DIALOGUE_PAIRS: list[tuple[str, str]] = [
    # ── Classroom ────────────────────────────────────────────────────────
    ("Could you explain that again, please?", "Of course, let me try a different approach."),
    ("What page are we on?", "We are on page forty-two, near the bottom."),
    ("Is this going to be graded?", "Yes, it counts towards your final mark."),
    ("Can I work with a partner on this?", "Absolutely, just make sure you both contribute equally."),
    ("Do we need to show our working?", "Yes, showing your steps is part of the assessment."),
    ("Can I hand it in tomorrow instead?", "I can give you one extra day, but no later than that."),
    ("I do not understand the question.", "Let me rephrase it in a simpler way for you."),
    ("Is there a word limit for this essay?", "Aim for between five hundred and eight hundred words."),
    ("Will this topic come up in the exam?", "It is worth knowing, so I would definitely revise it."),
    ("Can I borrow your notes?", "Sure, but make sure you return them before Friday."),
    ("When is the next assignment due?", "You have until the end of next week."),
    ("Is it okay to use online sources?", "Yes, as long as you cite them properly."),
    ("Can we discuss this in groups?", "That is a great idea — give yourselves ten minutes."),
    ("What does this term mean?", "It refers to the process of breaking something down into its parts."),
    ("Should I include an introduction?", "Yes, always start with a clear introduction."),
    ("How many references do we need?", "At least five, and they should be from academic sources."),
    ("Is it better to use first person or third person?", "Third person is more formal and usually preferred for academic writing."),
    ("Can you check my draft before I submit it?", "Leave it with me and I will have a look by tomorrow."),
    ("What happens if I miss the deadline?", "There is a late penalty, so it is better to submit something than nothing."),
    ("Should we write a conclusion?", "Yes, and it should do more than simply repeat what you have already said."),
    # ── Workplace ─────────────────────────────────────────────────────────
    ("Have you finished the report?", "Almost — I just need to check the final figures."),
    ("Do you think we should try a different method?", "That is a good idea — let us discuss it as a team."),
    ("Can you help me understand this diagram?", "Sure, let me walk you through it step by step."),
    ("Is the meeting still on for tomorrow?", "Yes, same time and same room."),
    ("Do you prefer working in a team or alone?", "It depends on the task, but I enjoy both."),
    ("Could you clarify the deadline for this?", "It needs to be done by close of business on Friday."),
    ("Should I copy the manager on this email?", "Yes, it is good to keep them in the loop."),
    ("How do we handle this client complaint?", "We acknowledge it quickly and offer a clear resolution."),
    ("Can you take notes during the meeting?", "No problem, I will send the summary by end of day."),
    ("I think there is a mistake in the report.", "Let me have a look — can you point out the section?"),
    ("Is the deadline flexible?", "Not really — the client is expecting it on Thursday."),
    ("Who is leading the project now?", "It has been reassigned to the senior team."),
    ("Can we get an update on the budget?", "I will pull the figures and share them before noon."),
    ("Should we loop in the design team?", "Good point — I will send them a message right away."),
    ("What is our top priority this week?", "Finishing the client presentation takes precedence."),
    ("Should we set up a weekly check-in?", "That sounds useful — I will send a recurring invite."),
    ("Who should sign off on this?", "It needs to go through the head of department first."),
    ("Can we move the standup to a different time?", "What time works better for you — I can adjust it."),
    ("How do we handle scope creep on this project?", "We document every change request and get written approval before proceeding."),
    ("What is the best way to escalate this?", "Email the line manager with a clear summary and proposed next steps."),
    # ── Technology ────────────────────────────────────────────────────────
    ("Why is my internet so slow today?", "It might be worth restarting your router."),
    ("How do I recover a deleted file?", "Check the recycle bin first — it may still be there."),
    ("What is the difference between saving and exporting?", "Saving keeps it in the original format; exporting converts it."),
    ("Is it safe to click on this link?", "If you do not recognise the sender, I would avoid it."),
    ("My laptop keeps overheating — what should I do?", "Make sure the vents are clear and try a cooling pad."),
    ("How do I set up two-factor authentication?", "Go to your account settings and look for the security section."),
    ("Should I update the software now or later?", "It is best to update soon — patches often fix security issues."),
    ("Can I share my screen with the team?", "Yes, just click the share button at the bottom of the window."),
    ("Why does the app keep crashing?", "Try clearing the cache or reinstalling the latest version."),
    ("Is cloud storage actually secure?", "It depends on the provider, but reputable services use strong encryption."),
    ("How do I free up space on my phone?", "Delete unused apps and move photos to cloud storage."),
    ("What is a VPN and do I need one?", "It encrypts your connection — useful on public networks."),
    ("How do I stop getting so many spam emails?", "Use your email filter and unsubscribe from unwanted lists."),
    ("Can I use this laptop offline?", "Yes, most applications will work without an internet connection."),
    ("What is the difference between a virus and malware?", "Malware is the broader category — a virus is one specific type."),
    ("How do I back up my files automatically?", "Set up cloud sync or schedule a regular backup with your operating system."),
    ("Why did my computer slow down after the update?", "Sometimes updates require a restart to complete — try rebooting first."),
    ("What is the safest browser to use?", "Most modern browsers are comparable — keeping it updated matters more."),
    ("How do I share a large file with someone?", "Use a cloud service like a shared folder link rather than email attachment."),
    ("Should I use the same password for everything?", "No — use a password manager and a unique password for each account."),
    # ── Healthcare ────────────────────────────────────────────────────────
    ("Are you feeling better today?", "A little, thank you — the rest really helped."),
    ("Did you take your medicine this morning?", "Yes, I took it right after breakfast."),
    ("Should I go to the doctor or wait and see?", "If it has lasted more than three days, I would get it checked."),
    ("Is it safe to exercise when you are sick?", "Light walking is usually fine, but avoid anything intense."),
    ("How long do I need to fast before the blood test?", "Typically eight to twelve hours — water is fine to drink."),
    ("Can I take both of these tablets at the same time?", "Check with your pharmacist to be sure there are no interactions."),
    ("What should I eat when I have an upset stomach?", "Plain food like rice, toast, and bananas is usually gentle."),
    ("How do I know if I am dehydrated?", "Dark urine, dry mouth, and feeling dizzy are common signs."),
    ("Is it normal to feel tired after starting this medication?", "Yes, fatigue can be a short-term side effect — it usually passes."),
    ("When should I see a specialist instead of my GP?", "Your GP will refer you if they think specialist care is needed."),
    ("How long will the recovery take?", "It varies, but most people feel better within a week or two."),
    ("Should I avoid any foods while taking this?", "Yes, check the leaflet — some medications interact with certain foods."),
    ("Can I drive while taking this medication?", "Check whether drowsiness is listed as a side effect — if so, avoid driving."),
    ("Is this dosage right for my age?", "Your GP will have calculated it based on your specific details."),
    ("How do I know if the treatment is working?", "Your symptoms should gradually improve — go back if they worsen."),
    ("Should I rest completely or stay gently active?", "Gentle movement is usually better than complete bed rest for most conditions."),
    ("Can stress make physical symptoms worse?", "Yes, stress has well-documented effects on the immune and digestive systems."),
    ("Is it okay to stop the antibiotics early if I feel better?", "No — always complete the full course to avoid antibiotic resistance."),
    ("What is the difference between a cold and the flu?", "Flu typically has a sudden onset and includes fever, body aches, and fatigue."),
    ("How much water should I be drinking each day?", "Around two litres is a general guide, though individual needs vary."),
    # ── Travel ────────────────────────────────────────────────────────────
    ("What is the best time of year to visit?", "Spring and autumn are usually the most pleasant seasons there."),
    ("How long is the flight?", "It is about eleven hours with one connection."),
    ("Do I need to book tours in advance?", "For popular attractions, definitely — they sell out quickly."),
    ("What currency do they use there?", "They use the local currency, so exchange some before you leave."),
    ("Is the tap water safe to drink?", "In most major cities, yes — but check for the specific region."),
    ("How do I get from the airport to the city centre?", "There is a direct train that runs every twenty minutes."),
    ("Should I get travel insurance?", "Always — it is worth it for peace of mind."),
    ("What is the local food like?", "It is absolutely delicious and very affordable."),
    ("Is it easy to get around without speaking the language?", "In tourist areas, many people speak English — apps help too."),
    ("How many days would you recommend for this city?", "Three to four days gives you a good feel for it."),
    ("Can I use my phone there without extra charges?", "Check with your network provider about international roaming."),
    ("Is it safe to travel there at the moment?", "It is worth checking the latest travel advisory before you go."),
    ("What should I do if I lose my passport?", "Contact your embassy or consulate immediately — they can help quickly."),
    ("How do I avoid tourist traps?", "Walk a few streets away from the main squares and eat where locals do."),
    ("Is it worth hiring a car?", "Only if you plan to travel outside the city — public transport is fine for most."),
    ("What are the visa requirements?", "It depends on your nationality — check the official government website."),
    ("Should I tip in restaurants?", "Tipping customs vary — in some countries it is expected, in others unusual."),
    ("How do I stay safe when travelling alone?", "Share your itinerary with someone at home and keep valuables out of sight."),
    ("What is the best way to deal with jet lag?", "Stay awake until local bedtime and get outside in natural light."),
    ("Are there any cultural customs I should know about?", "Dressing modestly and removing shoes in certain spaces are common requirements."),
    # ── Food ──────────────────────────────────────────────────────────────
    ("What is the recipe for this?", "It is actually quite simple — I will write it down for you."),
    ("How do you know when the pasta is ready?", "Taste it — it should be soft but still have a slight bite."),
    ("Can I substitute something for the cream?", "Coconut milk works really well as an alternative."),
    ("Why did my cake come out flat?", "The baking powder might have been expired or the oven too cool."),
    ("How spicy is this dish?", "It has a gentle warmth, but nothing too intense."),
    ("Should I let the meat rest before cutting it?", "Yes, a few minutes of resting keeps the juices in."),
    ("What herbs go well with chicken?", "Rosemary, thyme, and tarragon are all excellent choices."),
    ("How long does this keep in the fridge?", "Up to three days if stored in an airtight container."),
    ("Is this dish vegetarian?", "Yes, it contains no meat or fish."),
    ("What wine would pair well with this?", "A light white would complement the flavours nicely."),
    ("How do I stop onions from making me cry?", "Try chilling them first or cutting near running water."),
    ("Is it better to use butter or oil for this?", "Butter adds richness; oil works better at higher temperatures."),
    ("Can I freeze this after cooking?", "Yes, let it cool completely first and freeze within two hours."),
    ("How do I get the bread to form a crust?", "Place a tray of water in the oven — the steam helps the crust develop."),
    ("Why is my sauce too thin?", "Simmer it longer without a lid to let the liquid reduce."),
    ("What is the easiest way to peel garlic?", "Crush it with the flat of a knife — the skin comes off easily."),
    ("How do I season a cast iron pan?", "Coat it lightly with oil and bake it upside down for an hour."),
    ("Can I use dried herbs instead of fresh?", "Yes, but use about a third of the quantity as dried are more concentrated."),
    ("What is the best oil for high-heat cooking?", "Oils with a high smoke point, like avocado or refined coconut oil."),
    ("How do I know if the fish is fresh?", "It should smell like the sea, not strongly fishy, and the flesh should be firm."),
    # ── Shopping ──────────────────────────────────────────────────────────
    ("Do you have this in a larger size?", "Let me check the stockroom — I will be right back."),
    ("Is there a sale on at the moment?", "Yes, twenty percent off selected items until Sunday."),
    ("Can I return this if it does not fit?", "Yes, within thirty days with the receipt."),
    ("How long does delivery take?", "Standard delivery is three to five working days."),
    ("Is this covered by a warranty?", "It comes with a one-year manufacturer's warranty."),
    ("Can I pay in instalments?", "Yes, we offer an interest-free payment plan."),
    ("Do you offer gift wrapping?", "Yes, it is available at the checkout for a small additional charge."),
    ("Is the price negotiable?", "I can offer you a small discount if you are buying two."),
    ("How do I track my order?", "You will receive an email with a tracking link once it ships."),
    ("Do you have a student discount?", "Yes, show your student ID for ten percent off."),
    ("Can I collect this in store instead?", "Yes, click and collect is available at most of our branches."),
    ("What happens if it arrives damaged?", "Contact us within forty-eight hours and we will arrange a replacement."),
    ("Is this item in stock?", "I can see we have three left — shall I reserve one for you?"),
    ("Can I place an order over the phone?", "Yes, I can take your details now if you would like to proceed."),
    ("Is there a minimum spend for free delivery?", "Free delivery applies to orders over thirty pounds."),
    ("Do you price match with other retailers?", "Yes, bring us the lower price and we will match it."),
    ("Can I exchange this for a different colour?", "Of course, as long as we have your size in stock."),
    ("What is the easiest way to cancel my order?", "Log into your account and select cancel — it only takes a moment."),
    ("Is there a loyalty scheme I can join?", "Yes, sign up in store today and earn points on every purchase."),
    ("How do I know which size to order?", "Our size guide is on the product page — it is very detailed."),
    # ── Weather ───────────────────────────────────────────────────────────
    ("Should I bring a jacket?", "Definitely — it is forecast to turn cold this afternoon."),
    ("Is the storm going to be bad?", "They are expecting heavy rain and strong winds by evening."),
    ("What is the weather like there in July?", "It is warm and sunny, occasionally with an afternoon shower."),
    ("Why is it so humid today?", "A warm front has moved in from the south overnight."),
    ("Will the snow cause any travel disruptions?", "Some routes may be affected — check updates before you leave."),
    ("Is it safe to drive in these conditions?", "Visibility is poor, so drive slowly and leave extra distance."),
    ("Why does the weather change so quickly here?", "The proximity to the coast makes conditions quite unpredictable."),
    ("Do you think it will clear up by the afternoon?", "The forecast suggests a break in the clouds around three."),
    ("How do meteorologists predict the weather?", "They use data from satellites, weather stations, and computer models."),
    ("Is this weather normal for this time of year?", "It is a bit unusual — temperatures are running slightly above average."),
    ("How accurate are seven-day forecasts?", "Reasonably accurate for the first three days, less so beyond that."),
    ("What causes fog to form?", "When moist air near the ground cools rapidly, the water vapour condenses."),
    ("Will there be a frost tonight?", "There is a chance — temperatures are forecast to drop to just below zero."),
    ("Why does the wind feel colder than the actual temperature?", "Wind chill makes the air feel colder by drawing heat away from the skin faster."),
    ("Is this the wettest summer on record?", "It is among the wettest in recent decades, according to the latest figures."),
    # ── Family ────────────────────────────────────────────────────────────
    ("Are you going to your parents' place this weekend?", "Yes, it is my mum's birthday so we are all getting together."),
    ("How are the kids settling into their new school?", "Really well — they have already made some good friends."),
    ("Does everyone in your family live nearby?", "Most of us do, though my brother is abroad at the moment."),
    ("How do you manage the school run with two jobs?", "We take turns — it takes some planning but it works."),
    ("What do you do for family holidays?", "We usually go somewhere coastal — simple and relaxing."),
    ("Do your children enjoy reading?", "My youngest is obsessed with books at the moment."),
    ("How do you handle screen time with young children?", "We have set agreed times and stick to them fairly well."),
    ("Did your parents teach you to cook?", "My grandmother was the one who really got me into it."),
    ("How often do you visit your family?", "We try to get together at least once a month."),
    ("What is your family's favourite tradition?", "We always have a big meal together on Sunday afternoons."),
    ("How do you balance everyone's different schedules?", "A shared calendar helps enormously — we all update it as we go."),
    ("Do you have family rituals around the holidays?", "We always go for a walk on the morning of each holiday, whatever the weather."),
    ("How do you deal with disagreements within the family?", "We try to talk things through calmly and give everyone a chance to be heard."),
    ("What do your children want to be when they grow up?", "This week, one wants to be a vet and the other an astronaut."),
    ("How did you decide on your children's names?", "We each had a list and worked through them until we found the one we both loved."),
    # ── Hobbies ───────────────────────────────────────────────────────────
    ("How did you get into painting?", "A friend bought me a starter kit and I was hooked instantly."),
    ("How long have you been playing the guitar?", "About three years now — I still practice every day."),
    ("Do you write fiction or non-fiction?", "Mostly fiction, though I dabble in essays occasionally."),
    ("Is photography expensive to get into?", "It can be, but starting with a smartphone is perfectly fine."),
    ("What got you into hiking?", "A colleague convinced me to join a short trail walk — I was sold."),
    ("Do you knit or crochet?", "Both, actually — they use different techniques but complement each other."),
    ("Have you ever sold your artwork?", "Yes, I have sold a few pieces through a local gallery."),
    ("What kind of music do you play?", "Mostly jazz, but I enjoy classical pieces too."),
    ("How do you find time for your hobbies?", "I wake up an hour earlier — mornings are peaceful for creative work."),
    ("What is the hardest thing about learning a new instrument?", "Staying consistent in the early stages when progress feels slow."),
    ("Do you do any outdoor hobbies?", "Yes, I cycle at weekends and do a bit of gardening."),
    ("Have you tried any creative writing?", "I write short stories in my spare time — nothing serious yet."),
    ("What made you start collecting things?", "A single find at a car boot sale — then I could not stop."),
    ("Do you exhibit your work anywhere?", "I have taken part in a couple of open studio events."),
    ("How do you stay motivated when a project stalls?", "I give it a few days and come back with fresh eyes."),
    ("Is pottery harder than it looks?", "Absolutely — but the learning curve makes it all the more satisfying."),
    ("Have you entered any competitions?", "Yes, a local photography one — I did not win but it was a great experience."),
    ("What equipment do you recommend for a beginner?", "Start with the basics and only invest in more as you grow into the hobby."),
    ("How has your hobby changed over the years?", "It has become more intentional — less about output, more about process."),
    ("Do you follow any artists or makers for inspiration?", "Several — I find social media genuinely useful for creative discovery."),
    # ── Gaming ────────────────────────────────────────────────────────────
    ("What game are you playing at the moment?", "A really good open-world adventure — I have put hours into it."),
    ("Do you prefer single-player or multiplayer?", "Single-player for the story, multiplayer for the social side."),
    ("Is that game difficult?", "The early levels ease you in, but it gets quite challenging later on."),
    ("Do you stream your gameplay?", "I have done a little, but I mostly play just for the enjoyment."),
    ("What makes a game truly memorable?", "A great story, satisfying mechanics, and a world worth exploring."),
    ("How do speedrunners get so fast?", "They study every frame of the game to find the most efficient path."),
    ("Is gaming a good way to relieve stress?", "For many people, yes — it offers a real sense of escape."),
    ("What was the first game you ever played?", "A classic platformer on an old console — I have fond memories."),
    ("Do you prefer competitive or casual gaming?", "Casual mostly — I play to relax rather than to compete."),
    ("What do you think of the latest update?", "Mixed feelings — some improvements, but a few things feel worse."),
    ("Do you think games can be genuinely artistic?", "Absolutely — some tell stories in ways no other medium can."),
    ("How do you avoid spending too much on in-game purchases?", "I set a monthly limit and treat it like any other entertainment budget."),
    ("What genre do you spend most time in?", "RPGs mostly — I love the sense of progression and exploration."),
    ("Is online gaming as fun as playing in person?", "Different, but it has its own appeal — especially with good friends."),
    ("Do younger people have an advantage in competitive games?", "Reaction time helps, but game sense and experience count for a lot too."),
    # ── Internet ──────────────────────────────────────────────────────────
    ("Did you see that video going around?", "Yes, I saw it last night — it was incredibly well-made."),
    ("How do you avoid falling for misinformation online?", "Cross-check with multiple reliable sources before sharing anything."),
    ("Do you follow many people online?", "I try to keep my feed focused on things that genuinely interest me."),
    ("Have you tried podcasts instead of music for commuting?", "Yes — I have learned so much more since making the switch."),
    ("How do you manage being reachable all the time?", "I set specific times when I check messages and stick to them."),
    ("Is it better to send an email or a message?", "Email for anything formal; a message is fine for quick things."),
    ("What do you do when someone misunderstands your message?", "I clarify calmly and try to understand what led to the confusion."),
    ("How do you communicate clearly in writing?", "Be direct, keep sentences short, and always re-read before sending."),
    ("Do you think social media is good or bad overall?", "Like most tools, it depends entirely on how you use it."),
    ("How do you deal with negative comments online?", "I try not to engage — it rarely leads anywhere useful."),
    ("Have you ever taken a break from social media?", "Yes — it was quieter, and honestly quite refreshing."),
    ("What do you use for keeping notes and ideas?", "A simple notes app — the key is actually reviewing it regularly."),
    ("Do you think people share too much online?", "Sometimes — a bit of friction before posting can be a good thing."),
    ("How do you find new things to read or watch?", "Recommendations from people I trust are more reliable than algorithms."),
    ("What is your approach to managing notifications?", "Most are turned off — I check on my terms, not the app's."),
    # ── Science and environment ───────────────────────────────────────────
    ("Why did the experiment not work?", "The temperature was not controlled carefully enough."),
    ("How do we know the universe is expanding?", "We observe that distant galaxies are moving away from us."),
    ("What is the simplest way to reduce my carbon footprint?", "Eat less meat, fly less, and choose public transport where possible."),
    ("Why do seasons change?", "Because the Earth is tilted on its axis as it orbits the sun."),
    ("Is nuclear energy safe?", "Modern reactors have strong safety records, but waste remains a challenge."),
    ("What causes thunder?", "It is the rapid expansion of air heated by a lightning bolt."),
    ("How long does plastic take to decompose?", "Most plastic takes hundreds of years, some over a thousand."),
    ("Are electric vehicles actually better for the environment?", "Over their full lifecycle, yes — though manufacturing has a cost too."),
    ("Why is biodiversity so important?", "It keeps ecosystems stable and resilient against disruptions."),
    ("Can individuals really make a difference for the climate?", "Every action matters, and collective small changes add up significantly."),
    ("What happens to recycled material?", "It is sorted, processed, and made into new products — the system is imperfect but improving."),
    ("Is there a simple way to explain photosynthesis?", "Plants use sunlight to convert water and carbon dioxide into food and oxygen."),
    ("How does a vaccine work?", "It teaches the immune system to recognise a pathogen without causing the disease itself."),
    ("Why do we still have questions about dark matter?", "We know it exists from its gravitational effects, but have not yet directly detected it."),
    ("What is the most immediate threat from climate change?", "Extreme weather events, sea level rise, and disruption to food and water systems."),
    # ── Emotions and wellbeing ────────────────────────────────────────────
    ("How do you manage stress during busy periods?", "I try to take short breaks and focus on one thing at a time."),
    ("What helps you feel better when you are upset?", "A walk outside usually helps me clear my head."),
    ("How can we support a friend going through a tough time?", "Listen without judgement and let them lead the conversation."),
    ("Is it okay to talk about mental health at work?", "Increasingly yes — workplaces are becoming more open about it."),
    ("How do you know when you need to take a break?", "When small things start feeling overwhelming, that is usually the sign."),
    ("What do you do when you cannot sleep?", "I try to avoid screens and read something calming instead."),
    ("How do you stay motivated when things get hard?", "I remind myself of why I started and celebrate small progress."),
    ("Do you have any daily habits that help your mood?", "Morning exercise and a consistent sleep routine make a big difference."),
    ("How do you deal with criticism?", "I try to separate the message from the emotion and find what is useful."),
    ("What is your approach to staying positive?", "I focus on what I can control and try to appreciate small wins."),
    ("How do you handle situations where you have no control?", "I try to accept what I cannot change and focus energy on what I can."),
    ("What do you find most draining emotionally?", "Situations where I feel unheard or where communication breaks down."),
    ("How do you recover after a particularly hard week?", "Rest, time with people who energise me, and something completely unrelated to work."),
    ("Do you have any rituals that help you reset?", "A long walk with no phone always does it."),
    ("How do you help yourself through periods of low motivation?", "I reduce expectations temporarily and focus on just showing up."),
    # ── Communication ─────────────────────────────────────────────────────
    ("How do you start a difficult conversation?", "I try to choose the right moment and lead with empathy."),
    ("What do you do if someone is not listening?", "I pause and ask if now is a good time to talk."),
    ("Is it better to be direct or diplomatic?", "Both have their place — context usually guides the right approach."),
    ("How do you disagree respectfully?", "I acknowledge their point before explaining my own perspective."),
    ("What makes someone a great communicator?", "Clarity, listening well, and adapting to the audience."),
    ("How do you write a professional email quickly?", "Start with the key point, be concise, and always proofread."),
    ("How do you prepare for a big presentation?", "Know your material well, practise out loud, and anticipate questions."),
    ("What should you avoid in a job interview?", "Speaking negatively about former employers or being too vague."),
    ("How do you give feedback to someone who is defensive?", "Focus on the behaviour and the impact rather than the person."),
    ("What is the best way to ask for help?", "Be specific about what you need and make it easy for the other person to say yes."),
    ("How do you handle being talked over in a meeting?", "I pause, wait for a gap, and re-enter calmly and clearly."),
    ("What do you do when you have misread someone's tone?", "Acknowledge it and ask directly — most people appreciate the clarification."),
    ("How do you keep a conversation going when it stalls?", "I ask an open question about something they mentioned earlier."),
    ("Is silence in a conversation always a bad sign?", "Not at all — comfortable silence is a mark of genuine connection."),
    ("How do you keep email communication concise?", "State the request in the first line and move everything else to bullet points."),
    # ── Finance ───────────────────────────────────────────────────────────
    ("Should I start investing now or wait?", "The best time to start is usually as soon as you have an emergency fund in place."),
    ("What is the difference between a Stocks and Shares ISA and a Cash ISA?", "One holds investments; the other is essentially a tax-free savings account."),
    ("How do I start budgeting if I never have before?", "Track every purchase for one month first — the patterns will reveal themselves."),
    ("Is it worth paying off my mortgage early?", "Compare the mortgage rate to what your savings could earn — the maths guides the answer."),
    ("How much should I have in an emergency fund?", "Three to six months of essential outgoings is the standard recommendation."),
    ("What is dollar-cost averaging?", "It means investing a fixed amount at regular intervals regardless of market conditions."),
    ("Are index funds a good option for beginners?", "Many experts recommend them for their low costs and broad diversification."),
    ("How does inflation affect my savings?", "If your savings earn less than inflation, the purchasing power of your money falls."),
    ("What is the difference between a debit and a credit card?", "A debit card uses your own money; a credit card borrows money you repay later."),
    ("Should I pay off debt before saving?", "High-interest debt should usually be cleared first — then build your savings."),
    # ── Sport ─────────────────────────────────────────────────────────────
    ("How do athletes stay motivated during a long season?", "Clear goals, a supportive team environment, and good recovery habits all help."),
    ("What is the best way to avoid injury when starting to train?", "Build gradually, prioritise recovery, and listen to your body carefully."),
    ("How important is nutrition for performance?", "Critically important — what you eat directly affects your energy and recovery."),
    ("What makes a good coach?", "Technical knowledge, emotional intelligence, and the ability to get the best from each individual."),
    ("Is mental strength more important than physical ability at the elite level?", "At the top, the physical differences are small — mindset often decides."),
    ("How do you deal with a losing streak?", "Analyse without overreacting, keep training well, and trust the process."),
    ("What is periodisation in training?", "It is a structured approach to varying training load to peak at the right time."),
    ("How does sports psychology help athletes?", "It builds mental skills like focus, resilience, and composure under pressure."),
    ("What separates good athletes from great ones?", "Consistency, attention to detail, and the willingness to keep improving."),
    ("How do team sports develop life skills?", "Communication, accountability, dealing with setbacks, and working towards shared goals."),
    # ── Music ─────────────────────────────────────────────────────────────
    ("How do you choose what to listen to?", "Mood drives most of it — I have playlists for almost every state of mind."),
    ("Is music theory necessary to play an instrument?", "Not essential to start, but it becomes very useful as you progress."),
    ("How do you get over stage fright?", "Preparation is the best cure — the more you know the material, the calmer you feel."),
    ("What is the best way to practise when you are short on time?", "Focus on the difficult passages rather than playing things you already know."),
    ("How has streaming changed the music industry?", "It democratised access but significantly reduced per-stream revenue for artists."),
    ("Do lyrics matter as much as the music itself?", "They can carry completely different weight depending on the listener."),
    ("What makes a great live performance?", "Connection with the audience — technical perfection matters less than presence."),
    ("How do you find new music you enjoy?", "Following recommendations from people with similar taste works better than algorithms."),
    ("Is classical music harder to learn than popular music?", "The notation and technique demand more formal training, but both have their challenges."),
    ("What role does music play in cultural identity?", "It carries history, shared memory, and a sense of belonging that little else can replicate."),
    # ── Architecture ──────────────────────────────────────────────────────
    ("What makes a building feel welcoming?", "Scale, natural light, and the way it meets the ground all play a role."),
    ("How do architects account for how a building will age?", "Through material choices, maintenance planning, and designing for flexibility of use."),
    ("Is sustainable architecture more expensive?", "Often upfront, but the whole-life costs are usually lower."),
    ("What is the difference between a structural and an interior designer?", "One deals with how a building stands up; the other with how it feels inside."),
    ("How does planning permission work?", "You submit designs to the local authority who assess them against planning policy."),
    ("What is passive design?", "It uses orientation, insulation, and ventilation to regulate temperature without mechanical systems."),
    ("How do you renovate a listed building?", "Carefully — changes require consent and must respect the character of the building."),
    ("What is the most challenging part of designing a public building?", "Meeting the needs of many different users while keeping the space coherent."),
    ("How does architecture influence behaviour?", "Space affects how people move, interact, and feel — good design does this intentionally."),
    ("What is brutalism?", "An architectural movement using exposed concrete and bold geometric forms, prominent from the 1950s."),
    # ── Law ───────────────────────────────────────────────────────────────
    ("What is the difference between a solicitor and a barrister?", "Solicitors advise clients; barristers typically argue cases in higher courts."),
    ("How does small claims court work?", "It handles lower-value disputes with simplified procedures and no need for a lawyer."),
    ("What is legal aid?", "State-funded legal support for those who cannot afford private representation."),
    ("Can a verbal agreement be legally binding?", "Yes, though proving the terms can be difficult without written evidence."),
    ("What does without prejudice mean?", "It means a communication cannot be used as evidence in court proceedings."),
    ("How long does it take to get a court date?", "It varies widely — from weeks to over a year depending on the court and case type."),
    ("What is the burden of proof in a civil case?", "The claimant must show their case is more likely than not — the balance of probabilities."),
    ("What happens if I miss a court date?", "The court may proceed without you, which often leads to a judgment against you."),
    ("Is a contract valid without a witness?", "In most cases yes, but certain contracts — like wills — require witnessed signatures."),
    ("What is the difference between a fine and a penalty?", "In most contexts they are interchangeable, though a fine is usually a fixed financial sum."),
    # ── History ───────────────────────────────────────────────────────────
    ("How do we know what ancient civilisations were like?", "Through archaeology, written records, and material culture where it survives."),
    ("Was history always written by the victors?", "Often, yes — which is why historians now work hard to recover silenced perspectives."),
    ("What was daily life like in medieval Europe?", "Demanding and short by modern standards, but communities had rich social and cultural lives."),
    ("How significant was the printing press?", "Transformative — it enabled the rapid spread of ideas and is linked to the Reformation."),
    ("Why do we study history?", "To understand how we got here, avoid repeating mistakes, and appreciate the present."),
    ("Was the Roman Empire really in decline for centuries?", "Historians debate the timeline, but yes, it was a gradual process with many causes."),
    ("How do oral histories compare to written records?", "They capture experiences the written record misses, but require careful interpretation."),
    ("What caused the collapse of ancient civilisations?", "Usually a combination of climate, resource stress, internal conflict, and external pressures."),
    ("How reliable are ancient historical accounts?", "Patchy — bias, exaggeration, and gaps are common, so cross-referencing is essential."),
    ("Is there such a thing as an objective history?", "Historians aim for it, but every account involves choices about what to include and how."),
    # ── Arts ──────────────────────────────────────────────────────────────
    ("What makes art meaningful?", "When it creates a genuine connection between the work and the person experiencing it."),
    ("Should art always have a message?", "Not necessarily — some of the most powerful work resists straightforward interpretation."),
    ("How do you respond to art you do not understand?", "Sit with the discomfort — understanding often comes later, or the response itself is enough."),
    ("Is art subjective?", "Partly, but shared aesthetic and cultural frameworks mean some responses are more widely held."),
    ("How has art changed since the internet?", "Distribution has democratised, but so has the noise — discoverability remains a challenge."),
    ("What is the difference between fine art and commercial art?", "Fine art is made primarily for its own sake; commercial art serves a specific client purpose."),
    ("How do artists price their work?", "Time, materials, market position, and reputation all factor in — it is rarely straightforward."),
    ("What is the role of the arts in education?", "Creativity, critical thinking, and emotional intelligence are all developed through arts engagement."),
    ("Is public funding for the arts justified?", "The economic, social, and cultural returns are well-documented — the case is strong."),
    ("How do you know when a piece of work is finished?", "Often when removing anything more would take something away — though the line is subjective."),
    # ── Mental health ─────────────────────────────────────────────────────
    ("What should I do if I think a friend is struggling?", "Check in gently, listen without rushing to fix things, and ask what they need."),
    ("Is therapy effective?", "For most people and most conditions, yes — particularly evidence-based approaches like CBT."),
    ("How do I know if I need professional help?", "If your distress is persistent, affecting daily life, or feels unmanageable alone."),
    ("What is the difference between feeling sad and being depressed?", "Depression is more persistent, pervasive, and typically interferes significantly with daily function."),
    ("Can exercise really help with anxiety?", "Yes — regular physical activity is one of the most evidence-supported interventions available."),
    ("How do I find a therapist I can trust?", "Look for someone qualified, registered, and with experience in what you are dealing with."),
    ("What is mindfulness actually about?", "Paying deliberate, non-judgmental attention to the present moment."),
    ("Is it possible to have too much self-awareness?", "Rumination can tip into unhealthy territory — the aim is reflection, not self-criticism."),
    ("How do you build resilience?", "Through experience of overcoming difficulty, good relationships, and a sense of meaning."),
    ("What is the link between sleep and mental health?", "Bidirectional and strong — poor sleep worsens most conditions, and distress disrupts sleep."),
    # ── Transport ─────────────────────────────────────────────────────────
    ("Is cycling safe in cities?", "It is improving with better infrastructure, but conditions vary significantly by city."),
    ("What is the environmental impact of flying?", "Significant — aviation accounts for a notable share of transport-related emissions."),
    ("How does congestion charging work?", "Drivers pay a fee to enter a defined zone, which reduces traffic and funds alternatives."),
    ("What are the benefits of public transport over driving?", "Lower emissions, reduced road congestion, and often cheaper at scale."),
    ("How long do electric vehicle batteries last?", "Most are designed to retain around eighty percent capacity after a decade of use."),
    ("What is the future of self-driving vehicles?", "Progress is real but regulatory and safety challenges mean full autonomy is still some way off."),
    ("Why is rail travel often more expensive than flying?", "Infrastructure costs and pricing structures — though the full environmental cost of flying is underpriced."),
    ("How do cities reduce car dependency?", "Through investment in public transport, cycling, walking, and mixed-use development."),
    ("What makes a transport network equitable?", "Affordability, reliability, and coverage that serves everyone, not just dense urban areas."),
    ("Is high-speed rail worth the investment?", "The evidence from countries with it suggests yes — if demand and network design are right."),
    # ── Education policy ──────────────────────────────────────────────────
    ("Should university be free?", "The evidence on the effects of fees is complex — both access and quality are affected."),
    ("Are standardised tests a fair way to assess pupils?", "They measure some things well but miss much of what matters in a good education."),
    ("How should schools handle smartphone use?", "Clear policies, consistently enforced, with genuine discussion about why they exist."),
    ("What makes a great teacher?", "Deep subject knowledge, genuine care for pupils, and the ability to adapt."),
    ("How do we close the attainment gap?", "Early years investment, teacher quality, and removing barriers to learning outside school."),
    ("Is homework beneficial?", "For older pupils, well-designed homework helps — for younger children, the evidence is weaker."),
    ("Should arts subjects receive equal funding to STEM?", "A rounded education needs both — and the evidence for arts' benefits is strong."),
    ("How do we attract and retain great teachers?", "Pay, workload, autonomy, and genuine professional development all matter."),
    ("What is the purpose of education?", "A contested question — but most would include knowledge, capability, and citizenship."),
    ("Do smaller class sizes improve outcomes?", "The evidence is positive but modest — teacher quality matters more."),
]

# ════════════════════════════════════════════════════════════════════════════
# CONTENT SAFETY FILTER
# ════════════════════════════════════════════════════════════════════════════

_BLOCKED_TERMS: frozenset[str] = frozenset([
    "kill", "murder", "weapon", "gun", "bomb", "drug", "alcohol",
    "hate", "racist", "sex", "nude", "violence", "terror",
    "suicide", "blood", "hurt", "abuse", "illegal", "exploit",
    "threaten", "assault", "steal", "cheat", "fraud",
])

# ════════════════════════════════════════════════════════════════════════════
# GENERATOR CONFIG
# ════════════════════════════════════════════════════════════════════════════

DIFFICULTIES = ("beginner", "intermediate", "advanced")
_DIFF_WEIGHTS = (0.35, 0.40, 0.25)

STRATEGIES = [
    "structured", "standalone", "transition", "time", "filler",
    "question", "dialogue_q", "dialogue_a", "compound",
    "conditional", "comparison", "exclamation", "passive", "narrative",
    # New strategies
    "rhetorical_question", "aphorism", "anecdote_opener", "imperative",
    "hypothetical", "reported_speech", "causal_chain", "sensory",
    "analogy", "proverb_twist", "future_tense", "enumeration",
    "reflection", "definition", "news_headline",
]
STRATEGY_WEIGHTS = [
    28, 14, 8, 8, 6, 6, 4, 4, 5, 3, 2, 1, 2, 1,
    # New strategy weights
    3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
]


# ════════════════════════════════════════════════════════════════════════════
# ROW DATACLASS
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class Row:
    id: int
    english_text: str


# ════════════════════════════════════════════════════════════════════════════
# SENTENCE GENERATOR CLASS
# ════════════════════════════════════════════════════════════════════════════

class SentenceGenerator:
    """
    Produces an endless stream of unique, human-like English sentences.

    All generation is deterministic given the same seed, lazy (generator-based),
    and memory-bounded — only the dedup hash set grows with scale.

    v3 adds:
    - 12 new domains (finance, law, sport, music, education_policy,
      mental_health, architecture, transport, history, arts, and more)
    - 8 new generation strategies (rhetorical_question, aphorism,
      anecdote_opener, imperative, hypothetical, reported_speech,
      causal_chain, sensory, analogy, proverb_twist, future_tense,
      enumeration, reflection, definition, news_headline)
    - Greatly expanded linguistic banks, standalone pools, and dialogue pairs
    - Extended paraphrase map (80+ entries)
    """

    def __init__(self, seed: int = 42) -> None:
        self._rng = random.Random(seed)
        self._seen: set[int] = set()
        self._domain_names = list(DOMAINS.keys())

        self._standalone_pool: list[tuple[str, str]] = []
        for lst, tag in [
            (STANDALONE_BEGINNER, "beginner"),
            (STANDALONE_INTERMEDIATE, "intermediate"),
            (STANDALONE_ADVANCED, "advanced"),
            (STANDALONE_SOCIAL_MEDIA, "social"),
            (STANDALONE_CUSTOMER_SUPPORT, "support"),
            (STANDALONE_CHILD_FRIENDLY, "child"),
            (STANDALONE_INSTRUCTIONAL, "instructional"),
            (STANDALONE_STORYTELLING, "story"),
            (STANDALONE_NEWS, "news"),
            (STANDALONE_PHILOSOPHY, "philosophy"),
            (STANDALONE_SCIENCE_FACTS, "science_facts"),
        ]:
            for s in lst:
                self._standalone_pool.append((tag, s))
        self._rng.shuffle(self._standalone_pool)

        self._dialogue_qs = [q for q, _ in DIALOGUE_PAIRS]
        self._dialogue_as = [a for _, a in DIALOGUE_PAIRS]

    # ── Public ─────────────────────────────────────────────────────────

    def stream(self, total: int) -> Generator[Row, None, None]:
        produced = 0
        while produced < total:
            row = self._next_unique_row(produced + 1)
            if row is not None:
                produced += 1
                yield row

    # ── Dispatch ───────────────────────────────────────────────────────

    def _next_unique_row(self, row_id: int, max_attempts: int = 60) -> Optional[Row]:
        for _ in range(max_attempts):
            text = self._build_sentence()
            if not self._is_safe(text):
                continue
            h = self._hash(text)
            if h not in self._seen:
                self._seen.add(h)
                return Row(id=row_id, english_text=text)
        base = self._build_sentence()
        text = base.rstrip(".!?") + f" (note {row_id % 9973})."
        self._seen.add(self._hash(text))
        return Row(id=row_id, english_text=text)

    def _build_sentence(self) -> str:
        strategy = self._rng.choices(STRATEGIES, weights=STRATEGY_WEIGHTS, k=1)[0]
        dispatch = {
            "structured":        self._structured_sentence,
            "standalone":        self._standalone_sentence,
            "transition":        self._transition_sentence,
            "time":              self._time_sentence,
            "filler":            self._filler_sentence,
            "question":          self._domain_question,
            "dialogue_q":        self._dialogue_question,
            "dialogue_a":        self._dialogue_answer,
            "compound":          self._compound_sentence,
            "conditional":       self._conditional_sentence,
            "comparison":        self._comparison_sentence,
            "exclamation":       self._exclamation_sentence,
            "passive":           self._passive_sentence,
            "narrative":         self._narrative_sentence,
            # New strategies
            "rhetorical_question": self._rhetorical_question,
            "aphorism":          self._aphorism_sentence,
            "anecdote_opener":   self._anecdote_opener,
            "imperative":        self._imperative_sentence,
            "hypothetical":      self._hypothetical_sentence,
            "reported_speech":   self._reported_speech_sentence,
            "causal_chain":      self._causal_chain_sentence,
            "sensory":           self._sensory_sentence,
            "analogy":           self._analogy_sentence,
            "proverb_twist":     self._proverb_twist,
            "future_tense":      self._future_tense_sentence,
            "enumeration":       self._enumeration_sentence,
            "reflection":        self._reflection_sentence,
            "definition":        self._definition_sentence,
            "news_headline":     self._news_headline_sentence,
        }
        return dispatch[strategy]()

    # ── Strategies — original ─────────────────────────────────────────

    def _pick_difficulty(self) -> str:
        return self._rng.choices(DIFFICULTIES, weights=_DIFF_WEIGHTS, k=1)[0]

    def _pick_domain(self) -> tuple[str, dict]:
        name = self._rng.choice(self._domain_names)
        return name, DOMAINS[name]

    def _domain_parts(self, domain: dict, diff: str) -> tuple[str, str, str, str]:
        d = diff[0]
        return (
            self._rng.choice(domain["subjects"]),
            self._rng.choice(domain[f"verbs_{d}"]),
            self._rng.choice(domain[f"objects_{d}"]),
            self._rng.choice(domain[f"extras_{d}"]),
        )

    def _structured_sentence(self) -> str:
        _, domain = self._pick_domain()
        diff = self._pick_difficulty()
        subj, verb, obj, extra = self._domain_parts(domain, diff)
        t = self._rng.randint(1, 10)
        if t == 1:
            sent = f"{subj} {verb} {obj} {extra}"
        elif t == 2:
            sent = f"{subj} recently {verb} {obj} {extra}"
        elif t == 3:
            conj = self._rng.choice(CONJUNCTIONS)
            sent = f"{subj} {verb} {obj} {conj} the outcome was {extra}"
        elif t == 4:
            sent = f"After some thought, {subj.lower()} {verb} {obj} {extra}"
        elif t == 5:
            sent = f"It is interesting how {subj.lower()} {verb} {obj} {extra}"
        elif t == 6:
            sent = f"Remarkably, {subj.lower()} {verb} {obj} {extra}"
        elif t == 7:
            sent = f"In many cases, {subj.lower()} {verb} {obj} {extra}"
        elif t == 8:
            sent = f"Unexpectedly, {subj.lower()} {verb} {obj} {extra}"
        elif t == 9:
            sent = f"Despite the circumstances, {subj.lower()} {verb} {obj} {extra}"
        else:
            sent = f"Without hesitation, {subj.lower()} {verb} {obj} {extra}"
        return self._capitalise_clean(sent)

    def _standalone_sentence(self) -> str:
        _, text = self._rng.choice(self._standalone_pool)
        return self._capitalise_clean(self._light_paraphrase(text))

    def _transition_sentence(self) -> str:
        transition = self._rng.choice(TRANSITIONS)
        _, domain = self._pick_domain()
        diff = self._pick_difficulty()
        subj, verb, obj, _ = self._domain_parts(domain, diff)
        return self._capitalise_clean(f"{transition} {subj.lower()} {verb} {obj}.")

    def _time_sentence(self) -> str:
        phrase = self._rng.choice(TIME_PHRASES)
        _, domain = self._pick_domain()
        diff = self._pick_difficulty()
        subj, verb, obj, _ = self._domain_parts(domain, diff)
        return self._capitalise_clean(f"{phrase} {subj.lower()} {verb} {obj}.")

    def _filler_sentence(self) -> str:
        opener = self._rng.choice(FILLER_OPENERS)
        _, domain = self._pick_domain()
        diff = self._pick_difficulty()
        subj, verb, obj, _ = self._domain_parts(domain, diff)
        return self._capitalise_clean(f"{opener} {subj.lower()} {verb} {obj}.")

    def _domain_question(self) -> str:
        _, domain = self._pick_domain()
        diff = self._pick_difficulty()
        return self._rng.choice(domain[f"questions_{diff[0]}"])

    def _dialogue_question(self) -> str:
        return self._light_paraphrase(self._rng.choice(self._dialogue_qs))

    def _dialogue_answer(self) -> str:
        return self._light_paraphrase(self._rng.choice(self._dialogue_as))

    def _compound_sentence(self) -> str:
        _, d1 = self._pick_domain()
        _, d2 = self._pick_domain()
        diff = self._pick_difficulty()
        s1, v1, o1, _ = self._domain_parts(d1, diff)
        s2, v2, o2, _ = self._domain_parts(d2, diff)
        conj = self._rng.choice(CONJUNCTIONS)
        return self._capitalise_clean(f"{s1} {v1} {o1}, {conj} {s2.lower()} {v2} {o2}.")

    def _conditional_sentence(self) -> str:
        opener = self._rng.choice(CONDITION_OPENERS)
        _, domain = self._pick_domain()
        diff = self._pick_difficulty()
        subj, verb, obj, _ = self._domain_parts(domain, diff)
        middle = self._rng.choice(CONDITIONAL_MIDDLES)
        return self._capitalise_clean(f"{opener} {subj.lower()} {verb} {obj}, and {middle}")

    def _comparison_sentence(self) -> str:
        starter = self._rng.choice(COMPARISON_STARTERS)
        _, domain = self._pick_domain()
        diff = self._pick_difficulty()
        subj, verb, obj, extra = self._domain_parts(domain, diff)
        return self._capitalise_clean(f"{starter} {subj.lower()} {verb} {obj} {extra}")

    def _exclamation_sentence(self) -> str:
        opener = self._rng.choice(EXCLAMATION_OPENERS)
        _, domain = self._pick_domain()
        diff = self._pick_difficulty()
        obj = self._rng.choice(domain[f"objects_{diff[0]}"])
        extra = self._rng.choice(domain[f"extras_{diff[0]}"])
        return self._capitalise_clean((f"{opener} {obj} {extra}").rstrip(".") + "!")

    def _passive_sentence(self) -> str:
        _, domain = self._pick_domain()
        diff = self._pick_difficulty()
        subj, verb, obj, extra = self._domain_parts(domain, diff)
        be = "were" if " and " in obj else "was"
        return self._capitalise_clean(f"{obj.capitalize()} {be} {verb} by {subj.lower()} {extra}")

    def _narrative_sentence(self) -> str:
        story = self._rng.choice(STANDALONE_STORYTELLING)
        middle = self._rng.choice(NARRATIVE_MIDDLES)
        base = story.rstrip(".!?")
        return self._capitalise_clean(f"{base}, {middle}")

    # ── Strategies — new ──────────────────────────────────────────────

    def _rhetorical_question(self) -> str:
        return self._light_paraphrase(self._rng.choice(RHETORICAL_QUESTIONS))

    def _aphorism_sentence(self) -> str:
        return self._light_paraphrase(self._rng.choice(APHORISMS))

    def _anecdote_opener(self) -> str:
        opener = self._rng.choice(ANECDOTE_OPENERS)
        _, domain = self._pick_domain()
        diff = self._pick_difficulty()
        subj, verb, obj, extra = self._domain_parts(domain, diff)
        return self._capitalise_clean(f"{opener} {subj.lower()} {verb} {obj} {extra}")

    def _imperative_sentence(self) -> str:
        return self._light_paraphrase(self._rng.choice(IMPERATIVES))

    def _hypothetical_sentence(self) -> str:
        return self._light_paraphrase(self._rng.choice(HYPOTHETICALS))

    def _reported_speech_sentence(self) -> str:
        starter = self._rng.choice(REPORTED_SPEECH_STARTERS)
        _, domain = self._pick_domain()
        diff = self._pick_difficulty()
        subj, verb, obj, extra = self._domain_parts(domain, diff)
        return self._capitalise_clean(f"{starter} {subj.lower()} {verb} {obj} {extra}")

    def _causal_chain_sentence(self) -> str:
        _, d1 = self._pick_domain()
        _, d2 = self._pick_domain()
        diff = self._pick_difficulty()
        s1, v1, o1, _ = self._domain_parts(d1, diff)
        s2, v2, o2, e2 = self._domain_parts(d2, diff)
        connector = self._rng.choice(CAUSAL_CONNECTORS)
        return self._capitalise_clean(
            f"{s1} {v1} {o1}, {connector} {s2.lower()} {v2} {o2} {e2}"
        )

    def _sensory_sentence(self) -> str:
        opener = self._rng.choice(SENSORY_OPENERS)
        _, domain = self._pick_domain()
        diff = self._pick_difficulty()
        subj, verb, obj, extra = self._domain_parts(domain, diff)
        return self._capitalise_clean(f"{opener} {subj.lower()} {verb} {obj} {extra}")

    def _analogy_sentence(self) -> str:
        starter = self._rng.choice(ANALOGY_STARTERS)
        body = self._rng.choice(ANALOGY_BODIES)
        return self._capitalise_clean(f"{starter} {body}")

    def _proverb_twist(self) -> str:
        return self._light_paraphrase(self._rng.choice(PROVERB_TWISTS))

    def _future_tense_sentence(self) -> str:
        starter = self._rng.choice(FUTURE_STARTERS)
        _, domain = self._pick_domain()
        diff = self._pick_difficulty()
        subj, _, obj, extra = self._domain_parts(domain, diff)
        future_verb = self._rng.choice(["will", "is likely to", "may", "could", "is expected to"])
        verb_base = self._rng.choice(domain[f"verbs_{diff[0]}"])
        return self._capitalise_clean(
            f"{starter} {subj.lower()} {future_verb} {verb_base} {obj} {extra}"
        )

    def _enumeration_sentence(self) -> str:
        opener = self._rng.choice(ENUMERATION_OPENERS)
        body = self._rng.choice(ENUMERATION_LISTS)
        return self._capitalise_clean(f"{opener} {body}")

    def _reflection_sentence(self) -> str:
        starter = self._rng.choice(REFLECTION_STARTERS)
        _, domain = self._pick_domain()
        diff = self._pick_difficulty()
        subj, verb, obj, extra = self._domain_parts(domain, diff)
        return self._capitalise_clean(f"{starter} {subj.lower()} {verb} {obj} {extra}")

    def _definition_sentence(self) -> str:
        opener = self._rng.choice(DEFINITION_OPENERS)
        phrase = self._rng.choice(DEFINITION_PHRASES)
        return self._capitalise_clean(f"{opener} {phrase}")

    def _news_headline_sentence(self) -> str:
        starter = self._rng.choice(NEWS_HEADLINE_STARTERS)
        _, domain = self._pick_domain()
        diff = self._pick_difficulty()
        subj, verb, obj, extra = self._domain_parts(domain, diff)
        return self._capitalise_clean(f"{starter} {subj.lower()} {verb} {obj} {extra}")

    # ── Paraphrase ─────────────────────────────────────────────────────

    _PARAPHRASE_MAP: dict[str, list[str]] = {
        "always":       ["consistently", "regularly", "typically", "generally", "invariably"],
        "very":         ["quite", "really", "fairly", "rather", "particularly"],
        "good":         ["great", "excellent", "solid", "strong", "fine"],
        "important":    ["essential", "significant", "valuable", "key", "critical"],
        "often":        ["frequently", "regularly", "commonly", "usually", "routinely"],
        "show":         ["demonstrate", "reveal", "illustrate", "highlight", "indicate"],
        "get":          ["obtain", "receive", "acquire", "gain", "secure"],
        "make":         ["create", "produce", "develop", "build", "generate"],
        "use":          ["apply", "employ", "utilise", "leverage", "adopt"],
        "big":          ["large", "significant", "major", "substantial", "considerable"],
        "small":        ["minor", "little", "slight", "modest", "limited"],
        "happy":        ["pleased", "content", "delighted", "glad", "thrilled"],
        "difficult":    ["challenging", "demanding", "complex", "tough", "tricky"],
        "easy":         ["simple", "straightforward", "effortless", "manageable", "accessible"],
        "fast":         ["quickly", "rapidly", "swiftly", "promptly", "efficiently"],
        "new":          ["recent", "latest", "modern", "updated", "fresh"],
        "start":        ["begin", "initiate", "launch", "commence", "kick off"],
        "help":         ["assist", "support", "aid", "facilitate", "guide"],
        "see":          ["observe", "notice", "spot", "identify", "recognise"],
        "think":        ["believe", "consider", "feel", "reckon", "suppose"],
        "need":         ["require", "demand", "call for", "depend on", "rely on"],
        "learn":        ["discover", "understand", "grasp", "pick up", "absorb"],
        "keep":         ["maintain", "sustain", "continue", "preserve", "retain"],
        "old":          ["established", "traditional", "long-standing", "existing", "prior"],
        "many":         ["numerous", "several", "various", "multiple", "a range of"],
        "really":       ["genuinely", "truly", "actually", "indeed", "notably"],
        "just":         ["simply", "only", "merely", "precisely", "exactly"],
        "still":        ["continuing", "yet", "even now", "to this day", "as before"],
        "wrong":        ["incorrect", "mistaken", "inaccurate", "flawed", "erroneous"],
        "right":        ["correct", "accurate", "appropriate", "suitable", "valid"],
        "change":       ["adjust", "adapt", "modify", "revise", "transform"],
        "clear":        ["evident", "apparent", "obvious", "transparent", "understandable"],
        "work":         ["function", "operate", "perform", "succeed", "progress"],
        "best":         ["optimal", "most effective", "ideal", "top", "preferred"],
        "different":    ["alternative", "distinct", "varied", "diverse", "contrasting"],
        "enough":       ["sufficient", "adequate", "satisfactory", "suitable", "ample"],
        "local":        ["community-based", "nearby", "regional", "area", "neighbourhood"],
        "share":        ["distribute", "communicate", "pass on", "exchange", "relay"],
        # Extended entries
        "better":       ["improved", "stronger", "more effective", "superior", "more capable"],
        "worse":        ["weaker", "less effective", "more problematic", "diminished", "poorer"],
        "quickly":      ["rapidly", "swiftly", "promptly", "without delay", "at pace"],
        "slowly":       ["gradually", "steadily", "at a measured pace", "carefully", "over time"],
        "try":          ["attempt", "endeavour", "aim", "seek to", "work to"],
        "find":         ["discover", "identify", "locate", "uncover", "detect"],
        "ask":          ["enquire", "request", "seek to understand", "question", "raise"],
        "tell":         ["communicate", "explain", "convey", "express", "articulate"],
        "look":         ["examine", "review", "consider", "assess", "evaluate"],
        "move":         ["shift", "transition", "progress", "advance", "relocate"],
        "give":         ["provide", "offer", "supply", "present", "contribute"],
        "take":         ["adopt", "accept", "assume", "undertake", "pursue"],
        "put":          ["place", "position", "apply", "set", "establish"],
        "come":         ["arrive", "emerge", "develop", "result", "follow"],
        "go":           ["proceed", "advance", "move forward", "progress", "head"],
        "seem":         ["appear", "look", "feel", "suggest", "indicate"],
        "become":       ["develop into", "emerge as", "grow to be", "transform into", "evolve into"],
        "high":         ["elevated", "significant", "considerable", "substantial", "notable"],
        "low":          ["limited", "modest", "reduced", "minimal", "slight"],
        "long":         ["extended", "prolonged", "lengthy", "sustained", "enduring"],
        "short":        ["brief", "limited", "concise", "compact", "narrow"],
        "hard":         ["demanding", "challenging", "strenuous", "difficult", "rigorous"],
        "soft":         ["gentle", "flexible", "measured", "moderate", "careful"],
        "real":         ["genuine", "authentic", "actual", "true", "tangible"],
        "great":        ["considerable", "substantial", "significant", "impressive", "notable"],
        "full":         ["complete", "comprehensive", "thorough", "total", "whole"],
        "free":         ["unrestricted", "open", "accessible", "available", "unconstrained"],
        "simple":       ["straightforward", "basic", "clear", "accessible", "uncomplicated"],
        "complex":      ["intricate", "nuanced", "multifaceted", "elaborate", "layered"],
        "important":    ["crucial", "significant", "essential", "key", "fundamental"],
        "possible":     ["feasible", "achievable", "viable", "realistic", "attainable"],
        "able":         ["capable", "equipped", "positioned", "prepared", "ready"],
        "known":        ["recognised", "established", "documented", "identified", "acknowledged"],
        "common":       ["widespread", "prevalent", "frequent", "typical", "standard"],
        "useful":       ["valuable", "practical", "helpful", "effective", "beneficial"],
        "true":         ["accurate", "valid", "correct", "well-founded", "sound"],
        "fair":         ["equitable", "balanced", "just", "reasonable", "proportionate"],
    }

    def _light_paraphrase(self, text: str) -> str:
        words = text.split()
        for i, word in enumerate(words):
            clean = word.lower().rstrip(".,!?;:")
            if clean in self._PARAPHRASE_MAP and self._rng.random() < 0.20:
                punct = word[len(clean):]
                replacement = self._rng.choice(self._PARAPHRASE_MAP[clean])
                if word[0].isupper():
                    replacement = replacement.capitalize()
                words[i] = replacement + punct
        return " ".join(words)

    @staticmethod
    def _capitalise_clean(text: str) -> str:
        text = text.strip()
        if not text:
            return text
        text = text[0].upper() + text[1:]
        if text[-1] not in ".!?":
            text += "."
        while "  " in text:
            text = text.replace("  ", " ")
        return text

    @staticmethod
    def _hash(text: str) -> int:
        return int(hashlib.md5(text.encode("utf-8")).hexdigest()[:16], 16)

    @staticmethod
    def _is_safe(text: str) -> bool:
        lower = text.lower()
        return not any(term in lower for term in _BLOCKED_TERMS)
