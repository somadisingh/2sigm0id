```
QUALITY (sorted by avg error, lower is better)
interviewer               interviews  avg error  95% range  band exact  within 1  valid JSON  mismatch caught  contradiction caught  false contra/interview  questions  errors
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
glm-5.3 (low, prompt v1)  15          0.149      0.10-0.20  47%         87%       99%         100%             100% of 12            0.8                     9.0        0     

COST AND SPEED (full run = projected for the main experiment)
interviewer               $/interview  output tokens  thinking tokens  secs/interview  rate limit  full run $  full run time
----------------------------------------------------------------------------------------------------------------------------
glm-5.3 (low, prompt v1)  $0.022       1317           224              63.6            120/min     $40.33      2.5 h        

Actual spend for this file: $0.35

Note: 5 test users per model. This is a screening test: when two models' 95% ranges overlap, treat them as tied and decide on cost, speed and valid-JSON rate. Add --repeats 2 or more personas for a firmer answer.
```
