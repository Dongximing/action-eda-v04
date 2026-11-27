# Object check offline: 90 distinct (task, taken object) pairs

Answer key: the taken object's type equals the task's object (names). P(yes) >= 0.5 counts as yes.

## Wording `plain`: "The object this command takes is the object the task asks for."

- right object, answered yes: 43/53
- wrong object, answered no (would be blocked): 21/37
- unusable answers: 0

| task object | taken | pairs | answered no | mean P(yes) |
|---|---|---|---|---|
| plate | pan | 3 | 1 | 0.55 |
| tomato | pan | 3 | 2 | 0.39 |
| apple | tomato | 2 | 2 | 0.09 |
| cloth | towel | 2 | 0 | 0.87 |
| cup | mug | 2 | 0 | 0.79 |
| lettuce | tomato | 2 | 2 | 0.03 |
| pan | pot | 2 | 1 | 0.52 |
| soapbar | soapbottle | 2 | 2 | 0.30 |
| apple | potato | 1 | 1 | 0.01 |
| bowl | pot | 1 | 1 | 0.41 |
| cup | egg | 1 | 1 | 0.03 |
| cup | glassbottle | 1 | 1 | 0.46 |
| dishsponge | cloth | 1 | 0 | 0.51 |
| egg | pot | 1 | 0 | 0.71 |
| ladle | spoon | 1 | 0 | 0.72 |
| mug | cup | 1 | 0 | 0.64 |
| mug | egg | 1 | 1 | 0.05 |
| mug | kettle | 1 | 0 | 0.63 |
| plate | apple | 1 | 1 | 0.16 |
| plate | bowl | 1 | 0 | 0.67 |
| plate | bread | 1 | 1 | 0.03 |
| plate | kettle | 1 | 1 | 0.30 |
| plate | pot | 1 | 1 | 0.34 |
| pot | pan | 1 | 0 | 0.72 |
| potato | tomato | 1 | 0 | 0.71 |
| spatula | lettuce | 1 | 1 | 0.04 |
| tomato | lettuce | 1 | 1 | 0.06 |

## Wording `exact`: "The object this command takes is exactly the object named in the task (the same object name, ignoring its number)."

- right object, answered yes: 50/53
- wrong object, answered no (would be blocked): 22/37
- unusable answers: 0

| task object | taken | pairs | answered no | mean P(yes) |
|---|---|---|---|---|
| plate | pan | 3 | 1 | 0.53 |
| tomato | pan | 3 | 2 | 0.37 |
| apple | tomato | 2 | 2 | 0.06 |
| cloth | towel | 2 | 0 | 0.83 |
| cup | mug | 2 | 0 | 0.78 |
| lettuce | tomato | 2 | 2 | 0.01 |
| pan | pot | 2 | 1 | 0.48 |
| soapbar | soapbottle | 2 | 2 | 0.39 |
| apple | potato | 1 | 1 | 0.01 |
| bowl | pot | 1 | 1 | 0.36 |
| cup | egg | 1 | 1 | 0.02 |
| cup | glassbottle | 1 | 1 | 0.48 |
| dishsponge | cloth | 1 | 1 | 0.40 |
| egg | pot | 1 | 0 | 0.62 |
| ladle | spoon | 1 | 0 | 0.70 |
| mug | cup | 1 | 0 | 0.55 |
| mug | egg | 1 | 1 | 0.03 |
| mug | kettle | 1 | 0 | 0.63 |
| plate | apple | 1 | 1 | 0.08 |
| plate | bowl | 1 | 0 | 0.64 |
| plate | bread | 1 | 1 | 0.01 |
| plate | kettle | 1 | 1 | 0.19 |
| plate | pot | 1 | 1 | 0.33 |
| pot | pan | 1 | 0 | 0.67 |
| potato | tomato | 1 | 0 | 0.74 |
| spatula | lettuce | 1 | 1 | 0.02 |
| tomato | lettuce | 1 | 1 | 0.03 |

Requests: 180 new, 0 from cache; 124s in new requests. Server http://127.0.0.1:8000/v1/systemone.
