# AWS Cost Optimization Guide

## Region Strategy

### Current Configuration
- **Primary Region**: `us-east-1` (N. Virginia)
- **All Resources**: Deployed in the same region to avoid cross-region transfer costs

### Resources in us-east-1
✅ **Elastic Beanstalk**
- Application: `passport-photo-budget`
- Environment: `passport-photo-free`
- EC2 instances, Load Balancers, Auto Scaling Groups

✅ **Simple Email Service (SES)**
- Email sending for OTP verification
- 3 verified identities configured

✅ **S3 Buckets**
- Elastic Beanstalk deployment artifacts
- Application versions and logs

✅ **CloudWatch**
- Application logs and metrics
- Performance monitoring

✅ **EC2 Instances**
- Application servers managed by Elastic Beanstalk
- Currently: 1 running instance (i-02eaa744d491be54f)

## Cost Savings Achieved

### Cross-Region Transfer Cost Avoidance
- **Saved**: $0.02/GB for US cross-region transfers
- **Saved**: $0.09/GB for international transfers
- **Estimated Monthly Savings**: $1.20 - $5.40 for typical usage

### Data Transfer Patterns
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Upload   │───▶│  EC2 (us-east-1)│───▶│  SES (us-east-1)│
│   (Internet)    │    │   Processing    │    │   Email Send    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  S3 (us-east-1) │
                       │   Logs/Backups  │
                       └─────────────────┘
```

**All internal AWS service communication stays within us-east-1 = $0.00 transfer costs**

## Deployment Pipeline Checks

Our deployment pipeline now includes automated region consistency checks:

### Step 2: AWS Region Consistency Check
```bash
python check_aws_region_consistency.py
```

**Validates**:
- SES configuration region
- Elastic Beanstalk applications and environments
- S3 bucket locations
- CloudWatch log groups
- EC2 instance placement

**Prevents**:
- Accidental cross-region deployments
- Unexpected data transfer charges
- Performance issues from cross-region latency

## Cost Monitoring

### Current Resource Costs (Estimated)
- **EC2 t3.micro**: ~$8.50/month (free tier eligible)
- **Elastic Beanstalk**: $0 (management is free)
- **SES**: $0.10/1000 emails (first 62,000 free with EC2)
- **S3**: ~$0.50/month for deployment artifacts
- **Data Transfer**: $0 (all same-region)

**Total Estimated**: ~$9/month (or free with AWS Free Tier)

### Cost Optimization Best Practices

1. **Region Consistency** ✅
   - All resources in us-east-1
   - Automated validation in deployment pipeline

2. **Right-Sizing** ✅
   - t3.micro instances (free tier eligible)
   - Auto-scaling based on demand

3. **Storage Optimization** ✅
   - S3 lifecycle policies for old deployment artifacts
   - CloudWatch log retention policies

4. **Network Optimization** ✅
   - No cross-region traffic
   - Efficient image processing (resize before storage)

## Monitoring and Alerts

### Cost Alerts (Recommended)
```bash
# Set up billing alerts for:
# - Monthly spend > $20
# - Data transfer > 1GB/day
# - Unusual cross-region activity
```

### Performance Monitoring
- CloudWatch metrics for response times
- Application logs for processing efficiency
- User experience monitoring

## Future Considerations

### Multi-Region Strategy (If Needed)
If global expansion is required:

1. **Primary Region**: us-east-1 (North America)
2. **Secondary Region**: eu-west-1 (Europe)
3. **Tertiary Region**: ap-southeast-1 (Asia)

**Cost Impact**:
- Cross-region replication: ~$0.02/GB
- Multi-region management complexity
- Increased monitoring costs

### Cost vs. Performance Trade-offs
- **Single Region**: Lower cost, higher latency for distant users
- **Multi-Region**: Higher cost, better global performance
- **CDN Option**: CloudFront for static assets (middle ground)

## Validation Commands

```bash
# Check region consistency
python check_aws_region_consistency.py

# Monitor costs
aws ce get-cost-and-usage --time-period Start=2024-01-01,End=2024-01-31 --granularity MONTHLY --metrics BlendedCost

# Check data transfer
aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name NetworkOut --start-time 2024-01-01T00:00:00Z --end-time 2024-01-31T23:59:59Z --period 86400 --statistics Sum
```

---

**Last Updated**: December 26, 2024  
**Validated**: All resources confirmed in us-east-1  
**Status**: ✅ Cost-optimized, no cross-region charges