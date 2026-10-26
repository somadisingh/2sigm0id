```
QUALITY (sorted by avg error, lower is better)
interviewer               interviews  avg error  95% range  band exact  within 1  valid JSON  mismatch caught  contradiction caught  false contra/interview  questions  errors
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
glm-5.3 (low, prompt v1)  15          0.114      0.08-0.15  60%         93%       100%        100%             91% of 11             0.3                     9.1        0     
glm-5.3 (low, prompt v3)  15          0.156      0.12-0.20  53%         93%       99%         100%             91% of 11             0.6                     9.1        0     
glm-5.3 (low, prompt v2)  15          0.167      0.13-0.21  33%         93%       100%        67%              77% of 13             0.2                     9.5        0     

COST AND SPEED (full run = projected for the main experiment)
interviewer               $/interview  output tokens  thinking tokens  secs/interview  rate limit  full run $  full run time
----------------------------------------------------------------------------------------------------------------------------
glm-5.3 (low, prompt v1)  $0.023       1340           237              45.8            120/min     $41.19      2.5 h        
glm-5.3 (low, prompt v3)  $0.023       1261           197              37.7            120/min     $41.85      2.5 h        
glm-5.3 (low, prompt v2)  $0.025       1262           209              46.0            120/min     $45.79      2.6 h        

Actual spend for this file: $1.12

Note: 5 test users per model. This is a screening test: when two models' 95% ranges overlap, treat them as tied and decide on cost, speed and valid-JSON rate. Add --repeats 2 or more personas for a firmer answer.
```
