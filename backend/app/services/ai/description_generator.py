"""
Description Generation Module

Generates AI-powered descriptions and remediation suggestions for tickets.
"""

import logging
import time
from .config import model
from .logging_config import perf_logger, metrics

logger = logging.getLogger(__name__)


def generate_ai_description(ticket_item: dict) -> str:
    """
    Generate a comprehensive AI description with problem explanation and solutions.
    
    Args:
        ticket_item: Structured ticket data
        
    Returns:
        Generated description string, or None on failure
    """
    func_start = time.time()
    
    try:
        # Build context from ticket fields
        context_parts = []
        
        if "title" in ticket_item:
            context_parts.append(f"Title: {ticket_item['title']}")
        
        if "description" in ticket_item:
            context_parts.append(f"Description: {ticket_item['description']}")
        
        if "sub_issue_type" in ticket_item:
            context_parts.append(f"Issue Type: {ticket_item['sub_issue_type']}")
        
        if "category_bucket_hint" in ticket_item:
            context_parts.append(f"Category: {ticket_item['category_bucket_hint']}")
        
        if "location" in ticket_item:
            context_parts.append(f"Location: {ticket_item['location']}")
        
        if "due_date" in ticket_item:
            context_parts.append(f"Due Date: {ticket_item['due_date']}")
        
        context = "\n".join(context_parts)
        
        """# Generate semantic embedding for context enrichment
        encode_start = time.time()
        model.encode(context, convert_to_tensor=True)
        encode_time = time.time() - encode_start
        metrics.record_operation("description_encoding", encode_time * 1000)
        perf_logger.debug(f"[TIMING] generate_ai_description encoding took {encode_time*1000:.2f}ms")
        """
        # Build comprehensive response based on issue type
        issue_type = ticket_item.get("sub_issue_type", "").lower()
        
        explanation = f"Issue: {ticket_item.get('title', 'Ticket Issue')}\n"
        explanation += f"Due: {ticket_item.get('due_date', 'Not specified')}\n\n"
        
        # Generate contextual explanation
        explanation += "Problem Explanation:\n"
        if ticket_item.get("description"):
            explanation += ticket_item["description"] + "\n\n"
        
        # Add AI-generated solutions based on issue type
        explanation += "Potential Causes & Solutions:\n"
        explanation += _get_issue_remediation(issue_type)
        
        func_time = time.time() - func_start
        metrics.record_operation("generate_ai_description_total", func_time * 1000)
        perf_logger.debug(f"[TIMING] generate_ai_description() completed in {func_time*1000:.2f}ms")
        
        return explanation
        
    except Exception as e:
        func_time = time.time() - func_start
        logger.error(f"generate_ai_description() failed after {func_time*1000:.2f}ms: {e}")
        return None


def _get_issue_remediation(issue_type: str) -> str:
    """
    Get issue-specific remediation suggestions.
    
    Args:
        issue_type: The type of issue (e.g., "backup", "network", "access")
        
    Returns:
        Remediation suggestions string
    """
    remediation_map = {
        "backup": (
            "- Backup failure typically indicates: Storage capacity issues, agent/service failure, "
            "network interruption, or permissions problem\n"
            "- Remediation: Check backup agent status, verify storage access, review job logs, "
            "restart agent service, test network connectivity, confirm last restore point\n"
        ),
        "network": (
            "- Network issues stem from: Router/firewall misconfiguration, connectivity loss, "
            "DNS resolution failure, or IP conflicts\n"
            "- Remediation: Verify network connectivity, ping gateway, check DNS settings, "
            "restart network devices, review firewall rules, check IP configuration\n"
        ),
        "connectivity": (
            "- Connectivity problems caused by: Service outage, configuration issues, or device problems\n"
            "- Remediation: Test connectivity, verify service status, check device configuration, "
            "review network logs\n"
        ),
        "offline": (
            "- Offline issues result from: Power loss, network disconnection, or device failure\n"
            "- Remediation: Check power status, verify network connection, test device, review event logs\n"
        ),
        "dns": (
            "- DNS failures caused by: DNS server unavailability, misconfiguration, or network issues\n"
            "- Remediation: Check DNS server status, verify DNS records, flush DNS cache, "
            "test name resolution, restart DNS services\n"
        ),
        "performance": (
            "- Performance degradation caused by: High resource utilization, heavy processes, "
            "insufficient disk space, or bandwidth saturation\n"
            "- Remediation: Monitor CPU/RAM/Disk usage, identify resource hogs, optimize queries, "
            "clear cache/temp files, check network bandwidth, review application logs\n"
        ),
        "slow": (
            "- Slow performance issues result from: Resource constraints, network latency, or software issues\n"
            "- Remediation: Monitor system resources, check network latency, optimize software, "
            "clear temporary files, upgrade hardware if needed\n"
        ),
        "access": (
            "- Access problems result from: Incorrect permissions, account lockout, expired credentials, or 2FA issues\n"
            "- Remediation: Verify user permissions, check account status, reset password if needed, "
            "enable/disable 2FA, review access logs, check account lockout threshold\n"
        ),
        "permission": (
            "- Permission issues stem from: Incorrect ACLs, role assignments, or group memberships\n"
            "- Remediation: Review user permissions, check group memberships, verify role assignments, "
            "audit access controls\n"
        ),
        "login": (
            "- Login failures caused by: Wrong credentials, account lockout, or authentication service issues\n"
            "- Remediation: Verify credentials, check account status, restart auth services, "
            "verify authentication logs, check 2FA settings\n"
        ),
        "malware": (
            "- Security threats require: Immediate isolation, antivirus scanning, forensic analysis, and containment\n"
            "- Remediation: Isolate affected system, run full antivirus scan, update security definitions, "
            "review security logs, change credentials, check for lateral movement, engage incident response\n"
        ),
        "virus": (
            "- Virus infections need: Isolation, scanning, cleaning, and prevention measures\n"
            "- Remediation: Isolate system, run full AV scan, quarantine infected files, update signatures, "
            "restore from clean backup if necessary\n"
        ),
        "security": (
            "- Security incidents require: Investigation, containment, remediation, and prevention\n"
            "- Remediation: Assess incident scope, contain threat, remediate systems, change credentials, "
            "review security logs, implement preventive measures\n"
        ),
        "breach": (
            "- Data breaches require: Immediate response, containment, forensics, and notification\n"
            "- Remediation: Isolate affected systems, begin forensic investigation, contain exposure, "
            "notify affected parties, implement preventive measures\n"
        ),
        "email": (
            "- Email issues include: Phishing attacks, spam, delivery failures, or configuration problems\n"
            "- Remediation: Check email logs, verify DNS/MX records, scan for phishing/malware, "
            "review security policies, implement email filtering\n"
        ),
        "phishing": (
            "- Phishing attacks need: User awareness, email filtering, and incident response\n"
            "- Remediation: Alert users, isolate compromised accounts, scan for malware, "
            "check for credential abuse, implement stronger email filtering\n"
        ),
    }
    
    # Find matching remediation (fuzzy match on issue type)
    for key, remediation in remediation_map.items():
        if key in issue_type:
            return remediation
    
    # Default remediation for unknown types
    return (
        "- General troubleshooting: Verify current system status, check recent changes, review error logs, "
        "test connectivity, restart services\n"
        "- Remediation: Diagnose root cause, apply appropriate fixes based on findings, test resolution, "
        "document changes\n"
    )
