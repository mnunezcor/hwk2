
import streamlit as st
import pandas as pd
import requests
import re
import os
from datetime import datetime
import plotly.express as px

# SETTINGS
st.set_page_config(
    page_title="Airline Customer Feedback",
    page_icon="✈️",
    layout="wide"
)

DATA_FILE = "feedback.csv"
URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "openai/gpt-oss-20b"

ALLOWED = [
    "delays_disruptions",
    "staff_service",
    "cabin_experience",
    "baggage_airport",
    "price_booking",
    "other_unclear"
]

PROMPT = """
You analyze customer feedback for an airline.

Assign exactly ONE primary category.

CATEGORIES:
- delays_disruptions: Delays, cancellations, missed connections,
  and disruption handling.
- staff_service: Staff behavior, communication, helpfulness,
  and complaint resolution.
- cabin_experience: Seats, comfort, cleanliness, food,
  entertainment, and onboard experience.
- baggage_airport: Lost luggage, baggage delays, check-in,
  boarding, and airport ground operations.
- price_booking: Ticket prices, extra fees, refunds,
  booking issues, and perceived value.
- other_unclear: Too vague or does not fit another category.

Also assign ONE sentiment:
positive, negative, mixed, or unclear.

RULES:
- Choose the main issue, not every issue mentioned.
- Do not invent details.
- Do not use the rating to decide the category.
- Damaged seats and onboard amenities belong to cabin_experience.
- Refunds, fees, and booking issues belong to price_booking.
- Actual delays and cancellations belong to delays_disruptions.
- Choose the most important issue if several are mentioned.

Return ONLY:
CATEGORY: [category]
SENTIMENT: [sentiment]
REASON: [brief explanation]
"""

# LOAD AND SAVE FEEDBACK

columns = [
    "timestamp", "rating", "comment", "category",
    "sentiment", "reason", "review_required", "review_reason"
]

def load_feedback():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    return pd.DataFrame(columns=columns)


def save_feedback(data):
    data.to_csv(DATA_FILE, index=False)


# AI CLASSIFICATION

def classify_comment(comment):

    key = st.secrets.get("GROQ-API-KEY")

    if not key:
        return "api_error", "unclear", "API key not configured"

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": comment[:5000]}
        ]
    }

    try:
        response = requests.post(
            URL,
            headers=headers,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        answer = response.json()["choices"][0]["message"]["content"]

        category = re.search(r"CATEGORY:\s*([a-z_]+)", answer, re.I)
        sentiment = re.search(r"SENTIMENT:\s*([a-z_]+)", answer, re.I)
        reason = re.search(r"REASON:\s*(.*)", answer, re.I | re.S)

        if not category or not sentiment or not reason:
            return "api_error", "unclear", "Could not parse AI response"

        category = category.group(1).lower()
        sentiment = sentiment.group(1).lower()
        reason = reason.group(1).strip()

        if category not in ALLOWED:
            return "api_error", "unclear", "Invalid category"

        if sentiment not in ["positive", "negative", "mixed", "unclear"]:
            return "api_error", "unclear", "Invalid sentiment"

        return category, sentiment, reason

    except Exception as e:
        return "api_error", "unclear", str(e)


# MANUAL REVIEW RULES

SERIOUS_TERMS = [
    "unsafe", "safety", "injured", "injury", "assault",
    "harassment", "discrimination", "racist",
    "wheelchair", "disability", "medical emergency"
]


def check_review_required(comment, rating, category, sentiment):

    reasons = []

    if category == "api_error":
        reasons.append("AI classification failed")

    if category == "other_unclear":
        reasons.append("Unclear or uncategorized comment")

    if sentiment == "unclear":
        reasons.append("Sentiment is unclear")

    if any(term in comment.lower() for term in SERIOUS_TERMS):
        reasons.append("Potential serious customer concern")

    if rating <= 2 and sentiment == "positive":
        reasons.append("Rating and sentiment do not agree")

    if rating >= 4 and sentiment == "negative":
        reasons.append("Rating and sentiment do not agree")

    return len(reasons) > 0, "; ".join(reasons)


# NAVIGATION

st.title("✈️ Airline Customer Feedback")

page = st.sidebar.radio(
    "Navigate",
    ["Submit Feedback", "Owner Dashboard"]
)


# CUSTOMER FEEDBACK FORM

if page == "Submit Feedback":

    st.header("Share Your Experience")

    st.write(
        "We value your feedback. Tell us about your recent airline experience."
    )

    with st.form("feedback_form"):

        rating = st.slider(
            "How would you rate your experience?",
            1, 5, 3
        )

        comment = st.text_area(
            "Tell us more about your experience (optional)"
        )

        submitted = st.form_submit_button("Submit Feedback")

    if submitted:

        category = "no_comment"
        sentiment = "unclear"
        reason = "No written comment provided"
        review_required = False
        review_reason = ""

        if comment.strip():

            with st.spinner("Analyzing your feedback..."):

                category, sentiment, reason = classify_comment(
                    comment.strip()
                )

            review_required, review_reason = check_review_required(
                comment.strip(), rating, category, sentiment
            )

        new_feedback = pd.DataFrame([{
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rating": rating,
            "comment": comment.strip(),
            "category": category,
            "sentiment": sentiment,
            "reason": reason,
            "review_required": review_required,
            "review_reason": review_reason
        }])

        data = load_feedback()
        data = pd.concat([data, new_feedback], ignore_index=True)
        save_feedback(data)

        st.success("Thank you! Your feedback has been submitted.")

        if category == "api_error":
            st.warning(
                "Your feedback was saved, but AI analysis was unavailable. "
                "It has been flagged for manual review."
            )


# OWNER DASHBOARD

if page == "Owner Dashboard":

    st.header("Customer Feedback Dashboard")

    data = load_feedback()

    if data.empty:

        st.info("No customer feedback has been submitted yet.")

    else:

        data["rating"] = pd.to_numeric(data["rating"], errors="coerce")

        data["review_required"] = (
            data["review_required"]
            .astype(str)
            .str.lower()
            .isin(["true", "1"])
        )

        total_feedback = len(data)
        average_rating = data["rating"].mean()
        manual_reviews = int(data["review_required"].sum())

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Feedback", total_feedback)

        col2.metric(
            "Average Rating",
            f"{average_rating:.2f}/5"
            if pd.notna(average_rating) else "N/A"
        )

        col3.metric("Needs Manual Review", manual_reviews)

        st.divider()

        comments = data[
            (data["comment"].fillna("").str.strip() != "") &
            (data["category"] != "api_error")
        ]

        if not comments.empty:

            st.subheader("Feedback Volume by Category")

            category_counts = (
                comments["category"]
                .value_counts()
                .rename_axis("Category")
                .reset_index(name="Number of Comments")
            )

            fig1 = px.bar(
                category_counts,
                x="Category",
                y="Number of Comments",
                title="Number of Comments per Category"
            )

            st.plotly_chart(fig1, use_container_width=True)

            st.subheader("Average Rating by Category")

            rating_by_category = (
                comments.groupby("category")["rating"]
                .mean()
                .reset_index()
            )

            fig2 = px.bar(
                rating_by_category,
                x="category",
                y="rating",
                title="Average Customer Rating by Category",
                range_y=[0, 5]
            )

            st.plotly_chart(fig2, use_container_width=True)

        st.divider()

        st.subheader("Comments Requiring Manual Review")

        flagged = data[data["review_required"] == True]

        if flagged.empty:

            st.success("There are currently no comments requiring review.")

        else:

            st.write(f"{len(flagged)} comments need attention.")

            for _, row in flagged.iterrows():

                with st.expander(
                    f"Rating: {row['rating']}/5 | {row['category']}"
                ):

                    st.write("**Customer comment:**")
                    st.write(row["comment"])

                    st.write("**AI reason:**")
                    st.write(row["reason"])

                    st.write("**Why it was flagged:**")
                    st.write(row["review_reason"])

                    st.write("**Sentiment:**", row["sentiment"])
