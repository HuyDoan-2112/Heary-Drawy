# Heary Drawy: market research

> Background landscape research. Current game requirements are in [product.md](../product.md); this report is not an exhaustive originality/effectiveness claim or an implementation plan.

Research checked: 2026-10-10  
Status: initial landscape review, not an exhaustive competitor search  
Related report: [Technical research](technical-research.md)

## Executive finding

Heary Drawy has a meaningful product distinction, but we cannot substantiate a claim that no similar project exists. Existing products already cover descriptive-language practice, listening activities, painting rewards, multiplayer drawing, and AI drawing recognition.

The proposed distinction is the combination: two teammates communicate about a hidden object through live push-to-talk voice turns, draw what they hear, and receive AI-assisted feedback on specific features rather than artistic quality.

**Suggested positioning:**

> Heary Drawy is a cooperative voice-and-drawing game for children aged 5+. One child describes a hidden object and their teammate draws what they hear. AI assists with gentle, feature-level feedback on what was said and drawn.

Pitch it as an Education / EdTech communication-practice activity, not a diagnostic tool or a replacement for a speech therapist.

## 1. Product being compared

The user's proposed experience includes:

- Two children as teammates with a shared score.
- A Describer who sees a secret object and must describe it without naming it.
- A Drawer who hears their teammate live and draws their interpretation.
- Live push-to-talk: hold to speak, release to end the turn. This replaces the original recording-and-upload proposal; microphones are not always open.
- Feature icons and prewritten coaching, with at most 1-2 extra description turns.
- One voice clarification question and a voice answer.
- AI-assisted speech and drawing checks against curated object features.
- Child-facing 1-3 stars, a feature checklist, and one gentle tip.
- An interactive 3D object reveal after every round's feedback, letting children explore the object as a playful reward before continuing and swapping roles.
- Exact figures available only in a protected grown-ups area.
- Random initial roles and a role swap after every round.
- Private rooms joined with a three-shape code, room-local random pairing, and a bot for an odd player.
- An English, low-reading-demand interface.
- No public matchmaking, free chat, webcam, or video.

These are requirements, not implemented features. At the initial repository check, the project contained only its README. The first demo is a responsive HTTPS website used in Safari on two controlled player devices, one iPad and one iPhone, with one pair. Native iOS packaging and custom application-level rate limiting are deferred for that demo.

Live voice is intended to make peer interaction more immediate; increased engagement or educational benefit has not been measured. Audio reaches the partner before AI analysis, so live delivery is not pre-screened moderation.

The 3D reveal is a proposed engagement feature, not a verified market differentiator. This review did not establish whether competitors offer similar 3D rewards.

## 2. Closest verified product: Describe With Art

**Publisher:** Virtual Speech Center  
**Evidence:** [Official product page](https://www.virtualspeechcenter.com/app/describe_with_art_app)

### Published features

The publisher describes an app for preschool and elementary-school children practicing verbal description and following directions containing descriptive vocabulary. Its page lists:

- Receptive following-directions tasks with prerecorded directions.
- Expressive description tasks across categories such as food, objects, and animals.
- The ability for children to give directions to other users with the audio feature off.
- Paint-palette rewards that unlock a painting activity.
- Multiple students, randomization, alternate student turns, response tracking, and emailed results.

### Overlap

This is closer than a generic speech-practice app: it already connects describing, listening, child-friendly reinforcement, and painting.

### Proposed distinction

In Heary Drawy, the drawing is the listener's interpretation of a teammate's description and part of the communication loop. Painting is not simply a reward after another activity.

Heary Drawy also proposes private room pairing across devices, live, bounded child-to-child turns, one clarification question, shared scores, role swapping, and AI evidence extraction from speech and drawings.

**Evidence boundary:** the published page does not establish that Describe With Art has this complete loop. Absence from the page is not proof that a capability does not exist elsewhere in the product. Current app behavior and availability were not tested.

## 3. Closest descriptive-language comparison: Describe It To Me

**Publisher:** Smarty Ears  
**Evidence:** [Official product page](https://www.smartyearsapps.com/describe-it-to-me/)

### Published features

The publisher organizes description around six areas:

1. Category.
2. Function.
3. Parts.
4. Location.
5. Visual characteristics such as color, shape, and size.
6. Additional facts.

It describes receptive multiple-choice tasks, expressive verbal responses, facilitator-recorded correctness, multiple user profiles, stars/rewards, and progress reporting.

### Overlap

Structured feature prompts, receptive/expressive practice, rewards, and adult-facing reporting are not novel on their own.

### Proposed distinction

Heary Drawy makes the description useful to a peer completing a drawing task. Its proposed automated analysis works on spoken-turn evidence and drawings, rather than relying only on facilitator-marked correctness.

### Useful lesson

A structured feature vocabulary is a sound product foundation. However, function and category can be useful spoken clues without being directly visible in a drawing. Do not assume that every speech feature belongs in the visual rubric.

**Evidence boundary:** publisher descriptions establish advertised functionality, not independently measured educational effectiveness.

## 4. AI drawing comparison: Quick, Draw!

**Publisher:** Google  
**Evidence:** [Official game](https://quickdraw.withgoogle.com/)

### Published behavior

A player draws a requested object while a neural network tries to recognize it. The official page explicitly acknowledges that recognition does not always work. It also describes drawings contributing to a publicly shared doodling dataset.

### Overlap

AI recognition of rough sketches is an established interaction, not a new invention in Heary Drawy.

### Proposed distinction

Heary Drawy asks whether specific information was expressed and represented, rather than simply whether an AI can guess an object category. It also adds a cooperative, voice-first communication task.

### Useful lesson

Recognition mistakes must be part of the design. Do not blame a child for a model's uncertainty. The public drawing-dataset model is not an appropriate privacy default for this project.

## 5. Adjacent speech-learning comparison: Speech Blubs

**Evidence:** [Official website](https://speechblubs.com/)

The publisher describes speech-learning activities using child models and a speech-therapy-oriented positioning.

### Proposed distinction

Heary Drawy is primarily a cooperative peer activity involving describing, listening, questioning, and drawing. It should not borrow diagnostic or treatment-oriented marketing claims from adjacent products.

**Evidence boundary:** statements on the publisher's site are marketing claims, not independent proof of effectiveness. This review did not test the app or verify its claimed outcomes.

## 6. Adjacent drawing games: Gartic Phone and drawing telephone games

**References:** [Gartic Phone](https://garticphone.com/), [Gartic publisher](https://gartic.com/)

Drawing telephone and guess-the-drawing games are established adjacent categories. They demonstrate that descriptions and drawings can be a social game mechanic.

The Gartic Phone homepage was blocked during this research. The publisher site was accessible, but did not provide enough detail to verify the current game's complete feature set. Treat this as an adjacent comparison, not a fully verified feature-by-feature audit.

Heary Drawy's intended difference is the combination of young-child accessibility, bounded voice turns, adult-managed rooms, cooperative goals, and feature-level communication feedback.

## 7. Barrier games: existing activity, proposed digital adaptation

The concept is explicitly inspired by barrier games, where one participant has information hidden from another and must communicate it. The user's proposal uses that activity as its foundation.

This review did not establish an evidence base for Heary Drawy's educational outcomes. Some educational resource pages were inaccessible or unavailable during the check.

Use careful wording:

- Appropriate: "Inspired by classroom barrier games."
- Appropriate: "Designed to give children opportunities to practice describing, listening, and asking questions."
- Not established: "Our AI version is clinically proven."
- Not established: "The game improves language ability by a measured amount."

## 8. Differentiation worth preserving

| Proposed distinction | Why it matters | Qualification |
| --- | --- | --- |
| Drawing as evidence of interpretation | Connects what one teammate says to what another produces | A matching feature does not prove it came from the description |
| Cooperative shared feedback | Frames the task as teamwork, not an art competition | The reward policy still needs testing |
| Clarification and repair | Gives children a reason to ask and answer a useful question | Keep this in the core loop, not an optional late feature |
| Original live voice | Enables immediate peer interaction without requiring reading | Connection reliability, permissions, privacy, and turn controls are required |
| Feature-based AI assistance | Makes feedback more explainable than object guessing alone | Accuracy on child speech and drawings is unvalidated |
| Adult-managed private rooms | Supports classroom-style use without public matchmaking | A short shape code is not sufficient security |
| Role swaps | Gives both children opportunities to describe and listen | Bot partners must support both roles |

Do not rely on stars, analytics, object pictures, or descriptive prompts alone as novelty claims. Existing products already use these elements.

## 9. Product improvements suggested by the comparison

### Preserve communication rather than object guessing

Avoid "Did the AI recognize an apple?" as the main result. Prefer a concrete recap: "We heard a color clue. We spotted a round shape. Next time, tell your teammate what is on top."

The system must distinguish detected evidence from uncertain interpretation.

### Make repair central

The Drawer’s one clarification question and the Describer’s answer should remain part of the initial end-to-end prototype. This is a more distinctive educational interaction than a simple describe-and-draw loop.

### Offer age-appropriate scaffolding

Use large controls, replayable instructions, icons, a forgiving drawing tool, and an alternative to continuous hold-to-talk where needed. Question icons can support the voice question without replacing it.

### Keep the adult view descriptive

Report feature counts and interaction details, not diagnostic labels. Percentages should have explicit denominators and uncertainty caveats; they are game metrics, not validated measures of a child's ability.

### Define a plausible initial setting

**Hypothesis, not validated demand:** an adult-facilitated classroom or small-group activity is a plausible first setting because pairing and admission are already supervised. Teacher interviews are needed to assess setup time, device access, room noise, curriculum fit, and whether the activity is actually useful.

## 10. Claims policy for the pitch

### Safe, supportable claims

- Cooperative communication-practice game.
- Inspired by barrier games.
- Designed for children aged 5+.
- AI-assisted checks of curated features in speech and drawings.
- No public matchmaking, webcam, video, or free chat, when implemented as specified.
- A combination distinct from the published features of the products reviewed here.

### Claims to avoid for now

- First or only product of its kind.
- No competitors exist.
- Clinically proven, diagnostic, or therapeutic replacement.
- Objective or perfectly fair AI scoring.
- Demonstrated improvement in children's communication.
- "Safe for kids" solely because rooms are private.

## 11. Research limitations and next validation

This report is a product-landscape check, not a market-size study or commercial validation. It contains no verified pricing comparison, revenue analysis, customer interviews, or current hands-on competitor testing.

Search-engine access was partly blocked or returned poor results. Several educational pages and the Gartic Phone homepage could not be inspected. App-store availability, patents, trademarks, and unpublished or hackathon projects were not exhaustively checked.

Next useful steps:

1. Search app stores, education catalogs, and hackathon repositories for the complete voice-description-to-peer-drawing loop.
2. Test the closest products rather than relying only on their marketing pages.
3. Interview educators about facilitation, attention span, noise, and device constraints.
4. Test the communication loop with adults and synthetic examples first.
5. Before child research, resolve consent, provider eligibility, and data handling as described in the technical report.

## Sources

Sources were accessed during the initial audit on 2026-10-10. Pages and provider policies can change.

- Virtual Speech Center: [Describe With Art](https://www.virtualspeechcenter.com/app/describe_with_art_app).
- Smarty Ears: [Describe It To Me](https://www.smartyearsapps.com/describe-it-to-me/).
- Google: [Quick, Draw!](https://quickdraw.withgoogle.com/).
- Speech Blubs: [Official website](https://speechblubs.com/).
- Gartic: [Publisher website](https://gartic.com/); [Gartic Phone](https://garticphone.com/) was blocked during the check.

These sources support the product comparisons above. They do not establish Heary Drawy's effectiveness, absolute novelty, or market demand.
