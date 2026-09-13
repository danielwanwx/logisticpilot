# Restore Opus 4.6 access

**Restored September 12, 2026.** After the administrator completed the console workflow, the application's original `missing20-sandbox` profile successfully invoked `us.anthropic.claude-opus-4-6-v1` in `us-west-2`. Both Converse and ConverseStream returned real answers (10 input / 5 output tokens each), and GetInferenceProfile returned `ACTIVE` with Virginia, Ohio and Oregon destinations. The isolated business workspace now explicitly selects `opus46`. See the [application acceptance record](../audits/2026-09-12-opus-restoration.md).

The earlier denial was real: no identity-based policy allowed `bedrock:InvokeModel` for Opus, and GetInferenceProfile was also denied. A separate browser authentication issue was resolved by starting a fresh console login in the existing Chrome profile. The CLI session remained valid. These were distinct checks.

Before the administrator completed the change, the console showed Nova Pro and Nova 2 Lite policies. Its existing `Missing20DeveloperBoundary` was inspected: its regional restriction excludes both Bedrock invocation actions, so it did not need modification for this request. The policy below was prepared on the console review page. On resuming after the user's completion message, that page was signed out and effective Opus access was verified through the application role. The agent did not itself click Create policy and has not read back the final attached policy document; effective invocation is verified, exact post-change IAM configuration is not asserted. Do not broaden the application's IAM administration rights merely to inspect its policies.

## Administrator action

For future recovery, open IAM → Roles → `Missing20DeveloperRole` → Permissions using an administrator identity. Inspect existing policies before adding anything, to avoid duplicates. The following is the narrowly scoped review template prepared for `Missing20Opus46Inference`, **not an exported final policy**. Replace `ACCOUNT_ID` with the intended AWS account ID.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InvokeOpus46USProfile",
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
      "Resource": "arn:aws:bedrock:us-west-2:ACCOUNT_ID:inference-profile/us.anthropic.claude-opus-4-6-v1"
    },
    {
      "Sid": "InvokeOpus46DestinationsThroughProfile",
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
      "Resource": [
        "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-opus-4-6-v1",
        "arn:aws:bedrock:us-east-2::foundation-model/anthropic.claude-opus-4-6-v1",
        "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-opus-4-6-v1"
      ],
      "Condition": {
        "StringEquals": {
          "bedrock:InferenceProfileArn": "arn:aws:bedrock:us-west-2:ACCOUNT_ID:inference-profile/us.anthropic.claude-opus-4-6-v1"
        }
      }
    },
    {
      "Sid": "InspectOpus46Profile",
      "Effect": "Allow",
      "Action": "bedrock:GetInferenceProfile",
      "Resource": "arn:aws:bedrock:us-west-2:ACCOUNT_ID:inference-profile/us.anthropic.claude-opus-4-6-v1"
    }
  ]
}
```

The [AWS Opus 4.6 model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-anthropic-claude-opus-4-6.html) lists Oregon as a supported source region with Virginia, Ohio and Oregon destinations. The [inference-profile prerequisites](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-prereq.html) require permissions for the profile and its destination models. The [geographic inference guidance](https://docs.aws.amazon.com/bedrock/latest/userguide/geographic-cross-region-inference.html) confirms that `bedrock:InferenceProfileArn` is populated for foundation-model evaluations, which is why the condition belongs only on that statement. Verify the existing permissions boundary and any organization policy also permit this exact use; do not remove the boundary or grant general administrator access. Changing the console's selected region alone does not supply missing role permissions.

After the administrator applies the intended change, repeat one minimal request and one streaming application request with the original sandbox role. If a different error then identifies account-level model access or Anthropic use-case requirements, follow [AWS model-access guidance](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html). An IAM denial alone does not prove those additional requirements are missing.

## Application and comparison boundary

Select Opus explicitly only after invocation succeeds. Do not silently fall back to Nova. Historical Opus success does not prove current authorization, and a successful connectivity probe does not establish answer accuracy.

The existing [paired evaluation protocol](../research/2026-09-12-paired-evaluation-protocol.md) freezes Nova for both single-agent and Graph candidates. An Opus comparison needs a separately frozen model configuration and pricing/budget allowance before paid runs; do not mix models and attribute a quality change to multi-agent architecture. Native conversation history growth was corrected in the [runtime restoration](../audits/2026-09-12-runtime-restoration.md), independently of model selection.
