from __future__ import annotations

from pydantic import BaseModel

TERMS_AND_CONDITIONS = """
COMPANIS TERMS OF SERVICE AND LIABILITY DISCLAIMER

Last Updated: 2026-02-21

BY CREATING AN ACCOUNT AND USING COMPANIS, YOU ACKNOWLEDGE AND AGREE TO THE FOLLOWING TERMS:

1. AI-GENERATED CONTENT DISCLAIMER
Companis uses artificial intelligence to generate recipe suggestions, ingredient substitutions,
and nutritional information. AI-generated content may contain errors, inaccuracies, or omissions.
The recipes and suggestions provided are for informational and entertainment purposes only and
should NOT be considered professional dietary, medical, or nutritional advice.

2. ALLERGY AND DIETARY RESTRICTION WARNING
While Companis makes every effort to respect dietary preferences and allergies entered by users,
AI systems are inherently imperfect and may:
- Fail to identify all allergens in a recipe or ingredient
- Suggest ingredients or substitutions that contain undisclosed allergens
- Incorrectly classify an ingredient as safe for a specific dietary restriction
- Miss cross-contamination risks or hidden allergens in processed foods

USERS MUST INDEPENDENTLY VERIFY ALL INGREDIENTS AND RECIPES for safety, especially when
allergies, intolerances, or medical dietary restrictions are involved. Failure to do so
could result in serious illness or death.

3. USER RESPONSIBILITY
You are solely responsible for:
- Verifying all ingredients before preparation and consumption
- Checking all food labels for allergens and dietary compliance
- Ensuring recipes are appropriate for all household members' dietary needs
- Consulting qualified healthcare professionals regarding dietary restrictions
- Supervising the preparation of meals, especially for children or vulnerable individuals
- Confirming the safety and freshness of ingredients used

4. NO MEDICAL OR NUTRITIONAL ADVICE
Companis does not provide medical advice. Health goals, calorie estimates, and nutritional
information are approximate and should not replace guidance from qualified healthcare providers,
dietitians, or nutritionists. Do not use this application to manage medical conditions without
consulting your healthcare provider.

5. LIMITATION OF LIABILITY
TO THE MAXIMUM EXTENT PERMITTED BY LAW, COMPANIS AND ITS DEVELOPERS, OPERATORS, AND
AFFILIATES SHALL NOT BE LIABLE FOR:
- Any adverse health reactions, allergic reactions, illness, or injury resulting from the
  preparation or consumption of recipes or ingredients suggested by the application
- Any errors, omissions, or inaccuracies in AI-generated recipes, ingredient lists,
  substitutions, or nutritional information
- Any damages arising from reliance on the application's suggestions without independent
  verification
- Any loss, damage, or harm of any kind arising from the use of this application

6. INDEMNIFICATION
You agree to indemnify and hold harmless Companis and its operators from any claims, damages,
or expenses arising from your use of the application, including but not limited to any adverse
health effects resulting from recipes prepared using the application's suggestions.

7. ASSUMPTION OF RISK
You acknowledge that cooking and food preparation carry inherent risks, including but not limited
to foodborne illness, allergic reactions, and kitchen injuries. You assume all such risks when
using this application.

8. DATA AND PRIVACY
Your dietary preferences, health goals, ingredient data, and usage patterns are stored to
improve your experience. This data may be processed by third-party AI providers as configured
by the application. We do not sell personal data to third parties.

9. THIRD-PARTY INTEGRATIONS
Shopping cart features may integrate with third-party services. Companis is not responsible
for the accuracy, pricing, availability, or quality of products from third-party providers.

10. CHANGES TO TERMS
We reserve the right to modify these terms at any time. Continued use of the application
after changes constitutes acceptance of the modified terms.

BY CLICKING "I AGREE" OR CREATING AN ACCOUNT, YOU CONFIRM THAT YOU HAVE READ, UNDERSTOOD,
AND AGREE TO BE BOUND BY THESE TERMS OF SERVICE.
"""


class TermsAcceptance(BaseModel):
    accepted: bool
    version: str = "1.0"


class TermsResponse(BaseModel):
    terms_text: str
    version: str
