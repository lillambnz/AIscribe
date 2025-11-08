# AIscribe - Business Model & Distribution Strategy

## Distribution Models

### Option 1: SaaS (Recommended for Most Clinics)

**Multi-Tenant Cloud Platform**

**Pros**:
- Easiest for clinics (no IT infrastructure needed)
- Centralized updates and maintenance
- Lower barrier to entry
- Predictable revenue stream
- Easier to scale

**Cons**:
- Some clinics may have data sovereignty concerns
- Requires robust infrastructure
- Higher initial investment

**Pricing Model**:
```
Tier 1 - Solo Practitioner
- 1 doctor
- Up to 100 hours/month transcription
- $149 AUD/month
- Basic SOAP notes

Tier 2 - Small Clinic
- Up to 5 doctors
- Up to 500 hours/month transcription
- $599 AUD/month
- Advanced SOAP, entity extraction
- Email support

Tier 3 - Medium Practice
- Up to 15 doctors
- Up to 2000 hours/month transcription
- $1,499 AUD/month
- Custom templates
- Priority support
- API access

Tier 4 - Enterprise
- Unlimited doctors
- Unlimited transcription
- Custom pricing (from $3,999 AUD/month)
- Dedicated support
- Custom integrations
- PMS/EMR connectors
- On-premise option available
```

**Overage Charges**:
- $2 AUD per additional hour of transcription
- Billed monthly in arrears

### Option 2: On-Premise (Hospital/Large Practices)

**Self-Hosted Installation**

**Pricing Model**:
```
One-time Setup Fee: $10,000 - $25,000 AUD
- Initial installation
- Training (2 days on-site)
- Configuration
- Integration with existing systems

Annual License:
- Small (up to 10 users): $12,000 AUD/year
- Medium (up to 50 users): $36,000 AUD/year
- Large (50+ users): $60,000+ AUD/year

Includes:
- Software updates
- Email support
- Security patches

Optional Add-ons:
- Premium support: +30%
- Custom development: $200-350 AUD/hour
- On-site training: $2,500 AUD/day + travel
```

### Option 3: Hybrid Model

**SaaS + On-Premise Options**

- Offer both models
- Allow migration between models
- Premium pricing for on-premise
- Shared development roadmap

## Technical Implementation

### 1. Subscription Management System

Add subscription tracking to the database:

```python
# backend/app/models/subscription.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.sql import func
from app.core.database import Base

class SubscriptionPlan(Base):
    """Subscription plan definitions."""
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)  # Solo, Small, Medium, Enterprise
    price_monthly = Column(Float, nullable=False)
    hours_included = Column(Integer, nullable=False)
    max_users = Column(Integer, nullable=True)  # Null = unlimited
    features = Column(JSON, nullable=False)
    active = Column(Boolean, default=True)


class Subscription(Base):
    """Clinic subscriptions."""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False, unique=True)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id"), nullable=False)
    status = Column(String(20), nullable=False)  # active, suspended, cancelled
    current_period_start = Column(DateTime, nullable=False)
    current_period_end = Column(DateTime, nullable=False)
    cancel_at_period_end = Column(Boolean, default=False)

    # Stripe/payment integration
    stripe_customer_id = Column(String(255), nullable=True)
    stripe_subscription_id = Column(String(255), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class UsageRecord(Base):
    """Track usage for billing."""
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True)
    clinic_id = Column(Integer, ForeignKey("clinics.id"), nullable=False)
    month = Column(String(7), nullable=False)  # YYYY-MM
    hours_used = Column(Float, default=0.0)
    encounters_count = Column(Integer, default=0)
    storage_gb = Column(Float, default=0.0)
    created_at = Column(DateTime, server_default=func.now())
```

### 2. Payment Integration (Stripe)

```python
# backend/app/services/billing_service.py
import stripe
from app.core.config import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

class BillingService:
    @staticmethod
    async def create_customer(clinic_id: int, email: str, name: str):
        """Create Stripe customer."""
        customer = stripe.Customer.create(
            email=email,
            name=name,
            metadata={"clinic_id": clinic_id}
        )
        return customer

    @staticmethod
    async def create_subscription(customer_id: str, price_id: str):
        """Create Stripe subscription."""
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            payment_behavior="default_incomplete",
            payment_settings={"save_default_payment_method": "on_subscription"},
            expand=["latest_invoice.payment_intent"],
        )
        return subscription

    @staticmethod
    async def cancel_subscription(subscription_id: str, at_period_end: bool = True):
        """Cancel subscription."""
        if at_period_end:
            subscription = stripe.Subscription.modify(
                subscription_id,
                cancel_at_period_end=True
            )
        else:
            subscription = stripe.Subscription.delete(subscription_id)
        return subscription

    @staticmethod
    async def record_usage(subscription_item_id: str, quantity: int):
        """Record metered usage (for overage billing)."""
        usage_record = stripe.SubscriptionItem.create_usage_record(
            subscription_item_id,
            quantity=quantity,
            timestamp=int(time.time()),
        )
        return usage_record
```

### 3. Usage Tracking Middleware

```python
# backend/app/middleware/usage_tracking.py
from datetime import datetime
from sqlalchemy import select
from app.models.usage_record import UsageRecord
from app.models.encounter import Encounter

async def track_usage(db, encounter_id: int):
    """Track usage when encounter is finalized."""
    # Get encounter
    result = await db.execute(
        select(Encounter).where(Encounter.id == encounter_id)
    )
    encounter = result.scalar_one_or_none()

    if not encounter:
        return

    # Calculate duration in hours
    if encounter.started_at and encounter.ended_at:
        duration_seconds = (encounter.ended_at - encounter.started_at).total_seconds()
        hours = duration_seconds / 3600.0

        # Get or create usage record for this month
        month = encounter.started_at.strftime("%Y-%m")
        result = await db.execute(
            select(UsageRecord).where(
                UsageRecord.clinic_id == encounter.clinic_id,
                UsageRecord.month == month
            )
        )
        usage = result.scalar_one_or_none()

        if not usage:
            usage = UsageRecord(
                clinic_id=encounter.clinic_id,
                month=month,
                hours_used=0.0,
                encounters_count=0
            )
            db.add(usage)

        # Update usage
        usage.hours_used += hours
        usage.encounters_count += 1
        await db.commit()
```

### 4. Feature Gating

```python
# backend/app/core/features.py
from app.models.subscription import Subscription, SubscriptionPlan

class FeatureGate:
    @staticmethod
    async def can_use_feature(db, clinic_id: int, feature: str) -> bool:
        """Check if clinic's subscription includes a feature."""
        # Get subscription
        result = await db.execute(
            select(Subscription).where(Subscription.clinic_id == clinic_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription or subscription.status != "active":
            return False

        # Get plan
        result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == subscription.plan_id)
        )
        plan = result.scalar_one_or_none()

        if not plan:
            return False

        # Check feature
        return feature in plan.features

    @staticmethod
    async def check_usage_limit(db, clinic_id: int) -> dict:
        """Check if clinic is within usage limits."""
        # Get subscription
        result = await db.execute(
            select(Subscription).where(Subscription.clinic_id == clinic_id)
        )
        subscription = result.scalar_one_or_none()

        if not subscription:
            return {"allowed": False, "reason": "No subscription"}

        # Get plan
        result = await db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == subscription.plan_id)
        )
        plan = result.scalar_one_or_none()

        # Get current month usage
        month = datetime.now().strftime("%Y-%m")
        result = await db.execute(
            select(UsageRecord).where(
                UsageRecord.clinic_id == clinic_id,
                UsageRecord.month == month
            )
        )
        usage = result.scalar_one_or_none()

        hours_used = usage.hours_used if usage else 0.0

        return {
            "allowed": hours_used < plan.hours_included,
            "hours_used": hours_used,
            "hours_limit": plan.hours_included,
            "hours_remaining": max(0, plan.hours_included - hours_used),
            "overage": max(0, hours_used - plan.hours_included)
        }
```

### 5. Billing API Endpoints

```python
# backend/app/api/billing.py
from fastapi import APIRouter, Depends
from app.services.billing_service import BillingService
from app.core.features import FeatureGate

router = APIRouter()

@router.post("/subscribe")
async def create_subscription(
    plan_id: int,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Subscribe clinic to a plan."""
    clinic_id = current_user["clinic_id"]

    # Get plan
    plan = await db.get(SubscriptionPlan, plan_id)

    # Create Stripe customer
    customer = await BillingService.create_customer(
        clinic_id=clinic_id,
        email=current_user["email"],
        name=f"Clinic {clinic_id}"
    )

    # Create subscription
    subscription = await BillingService.create_subscription(
        customer_id=customer.id,
        price_id=plan.stripe_price_id
    )

    # Save to database
    db_subscription = Subscription(
        clinic_id=clinic_id,
        plan_id=plan_id,
        status="active",
        stripe_customer_id=customer.id,
        stripe_subscription_id=subscription.id,
        current_period_start=datetime.fromtimestamp(subscription.current_period_start),
        current_period_end=datetime.fromtimestamp(subscription.current_period_end)
    )
    db.add(db_subscription)
    await db.commit()

    return {
        "subscription_id": subscription.id,
        "client_secret": subscription.latest_invoice.payment_intent.client_secret
    }

@router.get("/usage")
async def get_usage(
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current usage and billing info."""
    clinic_id = current_user["clinic_id"]
    usage_check = await FeatureGate.check_usage_limit(db, clinic_id)

    return usage_check

@router.post("/cancel")
async def cancel_subscription(
    at_period_end: bool = True,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel subscription."""
    clinic_id = current_user["clinic_id"]

    # Get subscription
    result = await db.execute(
        select(Subscription).where(Subscription.clinic_id == clinic_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(404, "No active subscription")

    # Cancel in Stripe
    await BillingService.cancel_subscription(
        subscription.stripe_subscription_id,
        at_period_end=at_period_end
    )

    # Update database
    subscription.cancel_at_period_end = at_period_end
    if not at_period_end:
        subscription.status = "cancelled"
    await db.commit()

    return {"status": "cancelled"}
```

## Go-to-Market Strategy

### Phase 1: MVP Launch (Months 1-3)

**Target**: 5-10 pilot clinics

1. **Free Pilot Program**
   - Select 5-10 GP clinics in Sydney/Melbourne
   - Offer 3 months free in exchange for feedback
   - Hands-on onboarding and support
   - Gather testimonials and case studies

2. **Pricing**: Free during pilot

3. **Goals**:
   - Validate product-market fit
   - Identify bugs and usability issues
   - Collect success metrics (time saved, accuracy, etc.)
   - Build case studies

### Phase 2: Early Adopters (Months 4-12)

**Target**: 50-100 clinics

1. **Launch Offer**
   - 50% off first 3 months
   - Free onboarding and training
   - Extended support

2. **Marketing Channels**:
   - Medical conferences (RACGP, AMA events)
   - GP practice management groups
   - LinkedIn ads targeting practice managers
   - Medical practice consultants
   - Word of mouth from pilots

3. **Pricing**:
   - Solo: $75/month (normally $149)
   - Small: $299/month (normally $599)

4. **Goals**:
   - Reach $50k MRR
   - Establish brand in market
   - Build referral network

### Phase 3: Growth (Year 2)

**Target**: 500+ clinics

1. **Full Pricing Launch**

2. **Marketing**:
   - Content marketing (blog, case studies)
   - SEO for "medical transcription Australia"
   - Partner with PMS vendors (Best Practice, etc.)
   - Webinars for practice managers
   - Reseller program

3. **Distribution Channels**:
   - Direct sales (website self-serve)
   - Inside sales team (for medium/enterprise)
   - Reseller partners
   - PMS integrations

4. **Goals**:
   - $500k+ ARR
   - 20%+ month-over-month growth

## Customer Acquisition

### Self-Service (Solo & Small Clinics)

1. **Website**: aiscribe.com.au
2. **Free Trial**: 14 days, no credit card
3. **Onboarding**: Automated email sequence + video tutorials
4. **Conversion**: Credit card required after trial

### Sales-Assisted (Medium & Enterprise)

1. **Lead Generation**:
   - Demo request form
   - Contact sales button

2. **Sales Process**:
   - Discovery call (30 min)
   - Product demo (45 min)
   - Trial setup (2 weeks)
   - Proposal and contract
   - Onboarding (1-2 weeks)

3. **Sales Team**: Start with 1 founder, then hire

## Onboarding Process

### Automated (Solo/Small)

```
1. Sign up → Email verification
2. Create clinic profile
3. Add first user (doctor)
4. Guided product tour (Intercom/Pendo)
5. First transcription test
6. Payment setup
7. Ongoing tips via email
```

### White-Glove (Enterprise)

```
1. Contract signed
2. Kickoff call
3. Technical setup (1 week)
   - SSO configuration
   - Custom templates
   - PMS integration
4. Training session (2 hours, virtual or on-site)
5. Pilot with 2-3 doctors (2 weeks)
6. Full rollout
7. Weekly check-ins (first month)
```

## Compliance & Legal

### Australian Medical Software Requirements

1. **TGA Registration**:
   - AIscribe likely Class I software (lowest risk)
   - May not require TGA registration (check with lawyer)
   - Document as "clinical decision support tool"

2. **Privacy**:
   - Privacy Act 1988 compliance (already built in)
   - Privacy Impact Assessment (PIA)
   - Privacy policy for customers

3. **Terms of Service**:
   - Make clear: AI-generated drafts must be reviewed
   - Liability limited to subscription fees
   - Data ownership (clinic owns data)
   - Data portability
   - Termination and data deletion

4. **Professional Indemnity Insurance**:
   - Technology E&O insurance
   - Cyber liability insurance
   - $5-10M coverage

### Contracts

**SaaS Agreement**:
- Month-to-month or annual
- Auto-renewal
- 30-day cancellation notice
- Data retention after cancellation (30 days)

**Enterprise Agreement**:
- Custom terms
- SLA (99.5%+ uptime)
- Data processing agreement
- BAA equivalent (if needed)

## Revenue Projections

### Conservative Scenario (Year 1)

```
Month 1-3 (Pilot): 10 clinics × $0 = $0 MRR
Month 4-6: 25 clinics × $200 avg = $5,000 MRR
Month 7-9: 50 clinics × $300 avg = $15,000 MRR
Month 10-12: 100 clinics × $350 avg = $35,000 MRR

Year 1 ARR: ~$200,000
```

### Optimistic Scenario (Year 2)

```
Month 13-24: Grow to 500 clinics
Average: $400/month
MRR: $200,000
ARR: $2,400,000
```

## Key Metrics to Track

1. **Acquisition**:
   - Monthly sign-ups
   - Trial-to-paid conversion rate
   - Customer acquisition cost (CAC)

2. **Engagement**:
   - Hours transcribed per clinic
   - Active users per clinic
   - Feature adoption rate

3. **Revenue**:
   - Monthly recurring revenue (MRR)
   - Annual recurring revenue (ARR)
   - Average revenue per user (ARPU)

4. **Retention**:
   - Monthly churn rate (target: <5%)
   - Customer lifetime value (LTV)
   - Net revenue retention (target: >100%)

5. **Unit Economics**:
   - LTV:CAC ratio (target: >3:1)
   - Months to recover CAC (target: <12)
   - Gross margin (target: >70%)

## Competitive Positioning

**vs Dragon Medical (Nuance)**:
- ✅ Lower cost (1/10th the price)
- ✅ Australian data residency
- ✅ Modern UI
- ✅ Automated SOAP notes
- ❌ Less mature/established

**vs Manual Typing**:
- ✅ 5-10x faster documentation
- ✅ More accurate
- ✅ Reduces doctor burnout
- ❌ Learning curve

**vs Offshore Transcription Services**:
- ✅ Instant results (vs 24-hour turnaround)
- ✅ Data stays in Australia
- ✅ Lower cost long-term
- ✅ Better privacy/security

## Next Steps

1. **Immediate** (This Week):
   - Set up Stripe account
   - Implement subscription models
   - Add billing endpoints
   - Create pricing page

2. **Short-term** (This Month):
   - Build landing page (aiscribe.com.au)
   - Create demo video
   - Recruit 3-5 pilot clinics
   - Set up support system (Intercom)

3. **Medium-term** (3 Months):
   - Complete pilot program
   - Build case studies
   - Launch early adopter program
   - Hire first sales person

Would you like me to implement the subscription and billing features in the code?
