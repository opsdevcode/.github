# Security policy

OpsDevCode first-class repositories share this reporting path.

**Do not open a public GitHub issue for a vulnerability.**

Report via:

1. GitHub Security Advisories on the **repository that contains the code**
2. Email **security@opsdevcode.com**

Include impact, reproduction, affected version/commit/image digest, and whether
the finding is already public.

Expect acknowledgment within two business days.

## Where the code lives

| Surface | Report against |
| --- | --- |
| Repave engine, portal, operator, gates | `opsdevcode/repave` |
| Overpass runtime / state API | `opsdevcode/overpass` |
| Toll identity repo (runtime still partly in Repave) | `opsdevcode/toll` **and** `opsdevcode/repave` if the code is in Repave |
| Dispatch identity (assistant runtime still in Repave/Relay) | `opsdevcode/dispatch` **and** the runtime repo |
| Relay internal runtime | `opsdevcode/relay` |
| Production AWS/EKS | `opsdevcode/repave-aws-infra` |
| Company website | `opsdevcode/opdevcode-website` |
| Org GitHub governance | `opsdevcode/.github` |
| Convergence methodology | `opsdevcode/convergence` (docs; not product runtime) |

Product-specific SECURITY.md files may add runtime detail. They must not invent
a different reporting address.
