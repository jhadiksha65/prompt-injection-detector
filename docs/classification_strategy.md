\# Classification Strategy



\## Primary Classification Task



The system will use binary classification for prompt injection detection.



\- 0 = Benign

\- 1 = Malicious



\## Why Binary Classification?



The primary purpose of the detector is to determine whether an incoming prompt is safe or potentially malicious.



Binary classification is selected because it:

\- simplifies the initial detection task

\- requires less complex and more consistently labelled training data

\- is suitable for the available project timeframe

\- allows the system to focus on high-recall detection of malicious prompts



\## Threat-Type Metadata



For malicious prompts, the specific attack category will be retained as metadata:



\- Direct Prompt Injection

\- Jailbreak Payload

\- System/Prompt Leakage

\- Goal Hijacking



Benign prompts will be labelled as:



\- Benign



The attack category will be used for analysis and reporting rather than as the primary ML classification target.



\## Label Mapping



| Label | Meaning |

|---|---|

| 0 | Benign |

| 1 | Malicious |



\## Classification Objective



Given an input prompt, the classifier should determine whether it is:



Benign → Allow



or



Malicious → Flag / Block



The final decision may also consider the rule-based detection layer and risk-scoring mechanism.

