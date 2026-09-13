# Agents for Humans: multiple-submission rules for LogisticPilot and MedGuard

**Decision date:** 2026-09-13

**Official sources checked:** 2026-09-12

**Scope:** whether the same entrant or team may submit both projects, how shared/prior work affects eligibility, track and prize limits, required technology/evidence, and the official judging formula. This is a rules reading, not an organizer eligibility determination.

## Decisive answer

**Yes. The same entrant or team may submit both LogisticPilot (formerly The Missing 20) and MedGuard.** The Official Rules expressly say an entrant may submit “more than one Submission.” The condition is decisive: the two submissions must be “unique and substantially different,” and the Sponsor and Devpost decide that question in their sole discretion. The competition FAQ repeats this rule. [Official Rules — Multiple Submissions](https://agentsforhumans.devpost.com/rules) · [Official FAQ — Teams & Submissions](https://agentsforhumans.devpost.com/details/faqs)

Two genuinely separate products in logistics operations and medication safety have a credible basis for being substantially different if each has its own primary user, problem, end-to-end workflow, product experience, demo, architecture, repository package, and Strands agent behavior. That is an **inference**, not advance approval. A new name, different styling, or a domain-swapped version of the same project would not establish substantial difference.

The safest submission position is:

- submit each as a separate Devpost project;
- choose one track for each project;
- describe the distinct primary user, task, tools, decisions, and outcomes;
- disclose shared or pre-existing project-specific work in both submissions;
- identify shared infrastructure precisely and explain what was newly built for each project during the submission period; and
- retain dated evidence that each submitted project was created and built during August 10–September 14, 2026.

## Explicit rules versus conclusions drawn from them

| Question | What the official pages explicitly say | Decision / remaining uncertainty |
| --- | --- | --- |
| May one entrant submit both projects? | An entrant may submit multiple submissions; each must be unique and substantially different. Eligible individuals may also join more than one team or organization and may enter individually. | **Yes.** This directly permits two submissions by the same person or team, subject to the substantial-difference test. [Rules §§3–4](https://agentsforhumans.devpost.com/rules) |
| Is team size limited? | The FAQ says there is no team-size limit. A team or organization must appoint an eligible representative. | **No published team-size cap.** [Official FAQ](https://agentsforhumans.devpost.com/details/faqs) · [Rules §§3–4](https://agentsforhumans.devpost.com/rules) |
| May the projects share prior work or components? | Standard frameworks, libraries, starter templates, and AI coding assistants are allowed. Other pre-existing code/work must be disclosed. Each project must be newly created during the submission period, and the submitted work must have been built then. Open-source components are permitted when their licenses are followed and the submission enhances them. | **No official page sets a numerical overlap limit or expressly bans shared components.** Shared general infrastructure is therefore not automatically disallowed, but disclosure does not cure an old project being repackaged or two submissions being insufficiently different. [Rules — New Projects, IP](https://agentsforhumans.devpost.com/rules) · [FAQ — existing code](https://agentsforhumans.devpost.com/details/faqs) |
| Does renaming The Missing 20 to LogisticPilot make it new? | The FAQ says the project must be newly created in the window, “not an existing project you're repackaging.” | **No.** A rename has no eligibility effect. If The Missing 20 existed before August 10, the admissible boundary between allowed disclosed prior work and prohibited repackaging requires written organizer clarification. If it was first created after August 10, preserve proof and disclose any earlier incorporated work. [Official FAQ](https://agentsforhumans.devpost.com/details/faqs) |
| Can one project enter multiple tracks/categories? | The FAQ says a project may “only fall into one track.” It permits multiple projects spanning tracks if they are unique and substantially different. | **No for one project; yes for separate qualifying projects.** Pick each project’s track from its primary user. [Official FAQ](https://agentsforhumans.devpost.com/details/faqs) |
| Can one project win Grand Prize and a track prize? | The rules say, “A Project can win one (1) Prize.” | **No.** One project has a one-prize cap. [Rules §8](https://agentsforhumans.devpost.com/rules) |
| Is there a prize cap per person or team across two projects? | The published rule states a cap per **Project**, not per entrant, person, team, or organization. Prize money is paid to the individual entrant, team representative, or organization; the representative allocates a team prize. | **No entrant-wide cap was found.** It is reasonable to read each qualifying project as capable of winning at most one prize, but multiple wins by the same entrant should not be promised because the rules do not affirmatively guarantee them and organizer verification/discretion still applies. [Rules §8](https://agentsforhumans.devpost.com/rules) |

## Track and prize mechanics

Each project selects exactly one of **Everyday Agents**, **Professional Agents**, or **Good Neighbor Agents**. The Grand Prize is open to all eligible submissions; each track has Gold/Golden, Silver, and Bronze awards of $5,000, $3,000, and $2,000. The Grand Prize is $10,000. Because one project may win only one prize, a project cannot collect both the Grand Prize and a track prize. [Official Rules — Prizes](https://agentsforhumans.devpost.com/rules) · [Official Overview — Prizes](https://agentsforhumans.devpost.com/)

**Track selection inference:** LogisticPilot naturally maps to Professional Agents if its primary user is a logistics or operations professional. MedGuard’s track depends on its primary user: personal medication management points to Everyday Agents; a clinician/pharmacist workflow points to Professional Agents; a nonprofit/community medication-access workflow points to Good Neighbor Agents. The FAQ instructs entrants to choose by primary user, so this choice must follow MedGuard’s actual demonstrated workflow rather than a prize strategy. [Official FAQ — track selection](https://agentsforhumans.devpost.com/details/faqs)

## Shared and prior work: practical eligibility boundary

Local Git history checked on September 13 begins with commit `8185253` on August 24, 2026, inside the submission window. This supports the repository's dated development history; it does not independently prove that no incorporated work existed earlier. The Missing 20 → LogisticPilot is a disclosed rename of this same entry, not a claim to a second newly created project.

The published pages leave “substantially different” undefined and provide no code-overlap percentage. They also do not say whether code created during the submission window for one entry becomes prohibited prior work when reused in another. The following is therefore a conservative **inference** from the new-project, disclosure, ownership, and multiple-submission rules:

1. Common third-party frameworks and ordinary starter tooling are expressly allowed.
2. A shared entrant-owned utility, deployment scaffold, or generic agent harness is not expressly prohibited, but should be disclosed in both entries when it is project-specific rather than a standard tool.
3. The differentiated value cannot be mostly configuration, prompts, terminology, colors, or sample data. Each entry should have a materially distinct end-to-end task, agent/tool loop, product behavior, and outcome.
4. Every incorporated component must satisfy ownership and third-party license/authorization rules.
5. If either project substantially existed before August 10, written clarification is warranted before submission. The Official Rules require prospective entrants to request clarification before the deadline when a term may be ambiguous and state that the rules prevail over other hackathon materials. Questions may be sent to `support@devpost.com`. [Official Rules §11 and contact](https://agentsforhumans.devpost.com/rules)

## Required technology and evidence

| Item | Status under the official pages |
| --- | --- |
| Strands Agents SDK | **Required.** The project must be a new AI agent built with Strands Agents and must use it meaningfully enough to pass the Stage One viability screen. |
| End-to-end work for real people | **Required.** The agent must handle a real task end to end rather than merely chat about it. |
| AWS account | **Required by the FAQ** to participate/use Strands for this event. |
| AWS Builder ID | **Required submission field.** |
| Amazon Bedrock AgentCore | **Optional.** AgentCore deployment strengthens Technical Implementation but is explicitly not required. |
| Evaluation suite, eval report, or published test metrics | **Not listed as a requirement** in the Rules, Overview, Resources, or FAQ. Evals can substantiate working, non-trivial behavior and impact, but treating them as mandatory would be an inference. |
| Live demo URL | **Optional as a submission field**, but a live demo improves Technical Implementation. Separately, free judging/testing access must be supplied through a website, functioning demo, or test build until judging ends. |
| Public repository | **Required**, with necessary source/assets/instructions, README, and an MIT or Apache license visible in the repository About area. |
| Architecture diagram | **Required.** The FAQ recommends showing the interface, Strands agent loop, tools/integrations, AWS services actually used, and output. |
| Demo video | **Required**, public on YouTube or Vimeo, no more than five minutes, showing the working project and pitching the problem, audience, and importance. |
| Language | Submission materials must be English or include the required English translations. |

Sources: [Official Rules — Project and Submission Requirements](https://agentsforhumans.devpost.com/rules), [Official Overview — What to Build/Submit](https://agentsforhumans.devpost.com/), [Official Resources — required tools](https://agentsforhumans.devpost.com/resources), and [Official FAQ](https://agentsforhumans.devpost.com/details/faqs).

## Official judging weights and tie-breaker

Stage One is pass/fail: the project must fit the theme and reasonably apply the required event tools/APIs/SDKs. Stage Two uses five **equally weighted** criteria, in this official order:

1. **Technical Implementation** — skillful, genuine, working, non-trivial Strands use; live demo and/or AgentCore deployment strengthens it.
2. **Design** — a complete, coherent product experience.
3. **Potential Impact** — a credible, specific real problem and audience that the demonstrated solution actually addresses.
4. **Creativity & Originality** — creative, non-obvious Strands use and real problem-domain understanding.
5. **Presentation** — a clear end-to-end working video and understandable problem/user/importance pitch.

The rules do not publish separate numeric percentages. Equal weighting means an effective **20% per criterion before bonus points**; that percentage is arithmetic, not a quoted organizer weight. Optional qualifying builder.aws posts add 0.2 points each, up to 0.6, for Stage Two submissions. [Official Rules §6](https://agentsforhumans.devpost.com/rules)

Tie-breaking follows the criterion order: **Technical Implementation → Design → Potential Impact → Creativity & Originality → Presentation**. If entries remain tied on all five, the judges vote. Technical Implementation is therefore the first tie-breaker even though the five base criteria are equally weighted. [Official Rules — Tie Breaking](https://agentsforhumans.devpost.com/rules)

## Deadline and finality

The Submission Period ends **Monday, September 14, 2026 at 5:00 p.m. Pacific Time**; the Devpost schedule labels the time **PDT**. After the deadline, submissions cannot be changed except for narrow organizer-permitted corrections involving infringement, personal information, or inappropriate material. Drafts do not count as proof of receipt. [Official Rules §§1 and 5](https://agentsforhumans.devpost.com/rules) · [Official schedule](https://agentsforhumans.devpost.com/details/dates)

## Bottom-line risk call

Submitting both projects is expressly allowed. The material eligibility risks are whether each project was genuinely newly created during the window and whether the two are substantially different in substance. Shared tooling is not categorically prohibited, but the rules provide no safe overlap threshold. For LogisticPilot, the former The Missing 20 identity should be disclosed plainly; if any meaningful version predates August 10, obtain written clarification before the deadline. For both submissions, make the shared-work inventory and the separately built product/workflow inventory explicit enough that a reviewer can assess the distinction without inference.

No official source supports a requirement to deploy on AgentCore or publish evals, and no official source found imposes a prize cap across all projects owned by one person or team. Those are absences in the published rules, not guarantees about organizer discretion.

## Primary sources

- [Agents for Humans Official Rules](https://agentsforhumans.devpost.com/rules)
- [Agents for Humans Overview](https://agentsforhumans.devpost.com/)
- [Agents for Humans FAQ](https://agentsforhumans.devpost.com/details/faqs)
- [Agents for Humans Resources](https://agentsforhumans.devpost.com/resources)
- [Agents for Humans Schedule](https://agentsforhumans.devpost.com/details/dates)

## Existing local notes reviewed

- `docs/research/2026-08-30-devpost-official-requirements.md`
- `docs/research/2026-09-03-official-competition-rubric-check.md`
- `docs/research/2026-09-05-agents-for-humans-award-readiness.md`

Those notes correctly captured the deadline, core submission requirements, equal judging criteria, and AgentCore’s optional status. This note adds the explicit multiple-submission, one-track-per-project, shared/prior-work, and prize-limit analysis.
