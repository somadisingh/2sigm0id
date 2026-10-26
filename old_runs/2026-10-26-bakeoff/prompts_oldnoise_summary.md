```
QUALITY (sorted by avg error, lower is better)
interviewer               interviews  avg error  95% range  band exact  within 1  valid JSON  mismatch caught  contradiction caught  false contra/interview  questions  errors
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
glm-5.3 (low, prompt v1)  15          0.113      0.10-0.13  47%         100%      100%        100%             13% of 15             0.2                     9.2        0     
glm-5.3 (low, prompt v2)  15          0.113      0.09-0.14  60%         100%      100%        67%              31% of 13             0.2                     9.5        0     

COST AND SPEED (full run = projected for the main experiment)
interviewer               $/interview  output tokens  thinking tokens  secs/interview  rate limit  full run $  full run time
----------------------------------------------------------------------------------------------------------------------------
glm-5.3 (low, prompt v1)  $0.023       1306           223              48.8            120/min     $40.83      2.5 h        
glm-5.3 (low, prompt v2)  $0.025       1227           209              46.4            120/min     $45.16      2.6 h        

Actual spend for this file: $0.75

Note: 5 test users per model. This is a screening test: when two models' 95% ranges overlap, treat them as tied and decide on cost, speed and valid-JSON rate. Add --repeats 2 or more personas for a firmer answer.
```
