from typing import List, Dict, Any
from urllib.parse import urlparse
from .base import BaseStrategy
from .greenhouse import GreenhouseStrategy
from .ashby import AshbyStrategy
from .powertofly import PowerToFlyStrategy
from .generic import GenericStrategy
from .builtin import BuiltInStrategy
from .smartrecruiters import SmartRecruitersStrategy
from .vneuron import VneuronStrategy
from .linedata import LinedataStrategy
from .modiami import ModiamiStrategy
from .bamboohr import BambooHRStrategy
from .workday import WorkdayStrategy
from .workingnomads import WorkingNomadsStrategy
from .infor import InforStrategy
from .snaphunt import SnaphuntStrategy

def get_strategy(url: str) -> BaseStrategy:
    strategies = [
        InforStrategy(),
        SnaphuntStrategy(),
        WorkdayStrategy(),
        BambooHRStrategy(),
        SmartRecruitersStrategy(),
        WorkingNomadsStrategy(),
        BuiltInStrategy(),
        GreenhouseStrategy(),
        PowerToFlyStrategy(),
        LinedataStrategy(),
        VneuronStrategy(),
        ModiamiStrategy(),
        AshbyStrategy(),
        # Add more strategies here
    ]
    
    for strategy in strategies:
        if strategy.can_handle(url):
            return strategy
            
    return GenericStrategy()

def plan_strategies(urls: List[str]) -> List[Dict[str, Any]]:
    plan: List[Dict[str, Any]] = []
    for u in urls:
        s = get_strategy(u)
        # Use platform_name if available, otherwise strategy name
        platform = getattr(s, "platform_name", s.__class__.__name__.replace("Strategy", ""))
        
        # Improve naming for Generic strategy using domain
        if platform == "Generic":
            try:
                parsed = urlparse(u)
                domain = parsed.netloc
                if domain.startswith("www."):
                    domain = domain[4:]
                
                # Handle subdomain cases like jobs.company.com -> Company
                parts = domain.split('.')
                if len(parts) >= 2:
                    if parts[0] in ['jobs', 'careers', 'apply', 'myworkdayjobs']:
                        platform = parts[1].capitalize()
                    else:
                        platform = parts[0].capitalize()
                else:
                    platform = domain.capitalize()
            except:
                pass

        plan.append({
            "url": u, 
            "strategy": s.__class__.__name__.replace("Strategy", ""),
            "platform": platform
        })
    return plan
