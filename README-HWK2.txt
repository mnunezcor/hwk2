Airline Customer Feedback Analysis

Project Overview
This Streamlit application collects airline customer feedback through ratings and optional written comments. Written comments are analyzed using a large language model (LLM) through the Groq API.

The application categorizes comments, identifies sentiment, and flags feedback that may require human review.

Business Question
Which aspects of the passenger experience generate the most negative feedback, and which customer comments require human follow-up?

Feedback Categories
- 'delays_disruptions': Delays, cancellations, missed connections, and disruption handling.
- 'staff_service': Staff behavior, communication, helpfulness, and complaint resolution.
- 'cabin_experience': Seats, comfort, cleanliness, food, entertainment, and onboard experience.
- 'baggage_airport': Lost luggage, baggage delays, check-in, boarding, and airport ground operations.
- 'price_booking': Ticket prices, extra fees, refunds, booking issues, and perceived value.
- 'other_unclear': Feedback that is too vague or does not fit another category.

AI Analysis
The application uses the Groq API with the `openai/gpt-oss-20b` model to assign one primary category and one sentiment to each written comment.

Manual Review
Feedback is flagged for human review when:
- AI classification fails.
- The comment is unclear or uncategorized.
- The comment contains potentially serious customer concerns.
- The rating and identified sentiment strongly disagree.

Dashboard
The owner dashboard displays:
- Total feedback submissions.
- Average customer rating.
- Number of comments requiring manual review.
- Feedback volume by category.
- Average rating by category.
- Full comments flagged for manual review.

Technologies
Python, Streamlit, Pandas, Plotly, Requests, and the Groq API.

Limitations
This application is an educational prototype. AI classifications may be inaccurate and should be validated by a human. API availability and rate limits may affect classification. Feedback is stored in a local CSV file, so persistent storage is not guaranteed on Streamlit Community Cloud.

Deployment
The application is deployed using Streamlit Community Cloud. The Groq API key is stored in Streamlit Secrets and is not included in the public repository.