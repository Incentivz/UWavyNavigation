Given a known starting location $X_0$, for each IMU update $\Delta_{i}$, find $\hat{X}_i$, an estimate of the true location $X_i$
1. Update the current best estimate $\hat{X}_i$ by applying $\hat{X}_i = \hat{X}_{i-1} + \Delta_{i}$
1. Take a picture of the ground ${img}_{test}$:
    1. ${img}_{test}$ will have known scale based on focal length and altitude
    1. True drone position $X_i$ is at the centerpoint of ${img}_{test}$
1. Search the database for a slice of the ground ${img}_{ref}$ that best matches ${img}_{test}$, starting at point $\hat{X_i}$ and moving outward in a spiral pattern
1. If a match is found with confidence above a certain threshold, update the estimate  using the location of the matching slice $\hat{X}_i = \hat{X}_{img}$, otherwise leave the estimate as is.
1. Repeat until $\hat{X}_i$ reaches the target destination.

Here is how that would work in practice: