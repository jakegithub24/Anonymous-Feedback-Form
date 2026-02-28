# Training Feedback Form

The questions and field definitions for the survey are written below in YAML.
Edit this file and reload the home page to change the form.  Supported question
fields:

- `type`: "rating", "textarea" (or "text"), or "radio"
- `name`: unique identifier used in form submission
- `label`: text displayed to users
- optional `maxlength`, `placeholder`, `rows`, `options` (for radio)

```yaml
- type: rating
  name: content_quality
  label: Quality of the content
- type: rating
  name: clarity
  label: Clarity of explanations
- type: rating
  name: engagement
  label: Engagement level of visuals
- type: rating
  name: satisfaction
  label: Overall satisfaction
- type: rating
  name: apply_likelihood
  label: How likely are you to apply what you learned?

- type: textarea
  name: most_valuable
  label: What did you find most valuable?
  maxlength: 2000
  placeholder: "Share what stood out to you most in this training..."

- type: textarea
  name: improvements
  label: What improvements would you suggest?
  maxlength: 2000
  placeholder: "Your suggestions help us improve..."

- type: radio
  name: recommend
  label: Would you recommend this training to others?
  options:
    - Yes
    - No
```