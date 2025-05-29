from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.security import get_api_key
from app.models.webhook import DependencyFilePayload
from app.services.scanner.osv import scan_dependencies
from app.services.notification.email import send_vulnerability_notification

router = APIRouter(tags=["Scanning"])


@router.post("/scan", summary="Manually scan dependency file")
async def manual_scan(
    payload: DependencyFilePayload,
    background_tasks: BackgroundTasks,
    api_key: str = Depends(get_api_key),  # Protected endpoint
):
    """
    Manually scan a dependency file for vulnerabilities.
    This endpoint can be used for testing or ad-hoc scans.
    """
    try:
        logger.info(f"Manual scan requested for {payload.repository} on {payload.branch}")
        
        scan_result = await scan_dependencies(
            repository=payload.repository,
            branch=payload.branch,
            commit_sha=payload.commit_sha,
            file_type=payload.file_type,
            file_content=payload.file_content
        )
        
        if scan_result.has_vulnerabilities:
            background_tasks.add_task(
                send_vulnerability_notification,
                scan_result
            )
            
        return {
            "repository": scan_result.repository,
            "branch": scan_result.branch,
            "scan_date": scan_result.scan_date,
            "dependencies_count": scan_result.dependencies_count,
            "vulnerabilities_count": len(scan_result.vulnerabilities),
            "vulnerabilities_by_severity": scan_result.vulnerabilities_by_severity,
            "vulnerabilities": [
                {
                    "id": vuln.id,
                    "summary": vuln.summary,
                    "severity": vuln.severity,
                    "affected_packages": [
                        {
                            "name": pkg.name,
                            "ecosystem": pkg.ecosystem,
                            "affected_versions": pkg.affected_versions,
                            "fixed_versions": pkg.fixed_versions
                        } for pkg in vuln.affected_packages
                    ],
                    "references": [
                        {
                            "type": ref.type,
                            "url": str(ref.url)
                        } for ref in vuln.references
                    ]
                } for vuln in scan_result.vulnerabilities
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in manual scan: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in manual scan: {str(e)}")