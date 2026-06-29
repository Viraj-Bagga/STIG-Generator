class STIGRule:
    def __init__(self, data=None):
        if data is None:
            data = {}
        self.group_id = data.get("group_id", "")
        self.group_title = data.get("group_title", "")
        self.group_description = data.get("group_description", "")
        self.rule_id = data.get("rule_id", "")
        self.stig_id = data.get("stig_id", "")
        self.severity = data.get("severity", "medium")
        self.title = data.get("title", "")
        self.vuln_discussion = data.get("vuln_discussion", "")
        self.nist_control = data.get("nist_control", "")
        self.cci = data.get("cci", "")
        self.rationale = data.get("rationale", "")
        self.manual_check = data.get("manual_check", "")
        self.fix_text = data.get("fix_text", "")
        self.custom_fields = data.get("custom_fields", {})

    def to_dict(self):
        return {
            "group_id": self.group_id,
            "group_title": self.group_title,
            "group_description": self.group_description,
            "rule_id": self.rule_id,
            "stig_id": self.stig_id,
            "severity": self.severity,
            "title": self.title,
            "vuln_discussion": self.vuln_discussion,
            "nist_control": self.nist_control,
            "cci": self.cci,
            "rationale": self.rationale,
            "manual_check": self.manual_check,
            "fix_text": self.fix_text,
            "custom_fields": self.custom_fields.copy()
        }


class STIGBenchmark:
    def __init__(self, data=None):
        if data is None:
            data = {}
        # Changed fallbacks to blank strings to ensure forms start completely empty
        self.benchmark_id = data.get("benchmark_id", "")
        self.is_benchmark_file = data.get("is_benchmark_file", False)
        self.title = data.get("title", "")
        self.description = data.get("description", "")
        self.version = data.get("version", "")
        self.release_info = data.get("release_info", "")
        self.publisher = data.get("publisher", "")
        
        # Load rules
        self.rules = []
        rules_data = data.get("rules", [])
        for r in rules_data:
            if isinstance(r, STIGRule):
                self.rules.append(r)
            elif isinstance(r, dict):
                self.rules.append(STIGRule(r))

    def to_dict(self):
        return {
            "benchmark_id": self.benchmark_id,
            "title": self.title,
            "description": self.description,
            "version": self.version,
            "release_info": self.release_info,
            "publisher": self.publisher,
            "rules": [rule.to_dict() for rule in self.rules]
        }