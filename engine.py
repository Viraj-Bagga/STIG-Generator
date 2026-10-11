import xml.sax.saxutils as saxutils
import xml.etree.ElementTree as ET
import re
from models import STIGBenchmark, STIGRule

# Used when a benchmark has no ID of its own. Group and rule IDs that are left
# blank are derived from the benchmark ID, so nothing product-specific is baked in.
DEFAULT_BENCHMARK_ID = "xccdf_org.example_benchmark"

# Empty sub-elements written after VulnDiscussion in each rule description, in the
# order the published STIG convention uses, so readers that expect them find them.
DESCRIPTION_PLACEHOLDERS = (
    "FalsePositives", "FalseNegatives", "Documentable", "Mitigations",
    "SeverityOverrideGuidance", "PotentialImpacts", "ThirdPartyTools",
    "MitigationControl", "Responsibility", "IAControls",
)


def _id_prefix(benchmark_id):
    """'xccdf_org.example_benchmark' -> 'xccdf_org.example'."""
    bid = benchmark_id or DEFAULT_BENCHMARK_ID
    return bid[: -len("_benchmark")] if bid.endswith("_benchmark") else bid


def _product_slug(prefix):
    """'xccdf_org.example' -> 'example', for the manual check system URN."""
    tail = prefix.rsplit(".", 1)[-1]
    return re.sub(r"[^a-z0-9-]+", "-", tail.lower()).strip("-") or "product"


def remove_namespaces(elem):
    """Recursively strips namespaces from the tags of an XML tree elements."""
    if '}' in elem.tag:
        elem.tag = elem.tag.split('}', 1)[1]
    for child in elem:
        remove_namespaces(child)


def _xe(text):
    """XML-escape text for element content."""
    return saxutils.escape(str(text or ""))


def _attr(text):
    """XML-escape text for use inside double-quoted attribute values."""
    return saxutils.escape(str(text or ""), {'"': '&quot;'})


def _cdata_safe(text):
    """Make text safe to embed inside a CDATA block (escape the ]]> terminator)."""
    return (str(text) if text else "").replace("]]>", "]]]]><![CDATA[>")


def parse_benchmark_xml(file_path):
    """Parses a STIG XCCDF XML file into a STIGBenchmark object."""
    tree = ET.parse(file_path)
    root = tree.getroot()
    remove_namespaces(root)

    if root.tag != "Benchmark":
        if root.tag == "Group":
            bench = STIGBenchmark()
            rule_obj = parse_group_element(root)
            if rule_obj:
                bench.rules.append(rule_obj)
            return bench
        raise ValueError(f"Root XML element '{root.tag}' is not a Benchmark or Group")

    # <status date="...">text</status> maps to release_info (date) and publisher (text)
    status_el = root.find("status")
    status_text = ""
    status_date = ""
    if status_el is not None:
        status_text = (status_el.text or "").strip()
        status_date = status_el.attrib.get("date", "")

    bench_data = {
        "benchmark_id":      root.attrib.get("id", ""),
        "is_benchmark_file": True,
        "title":             root.findtext("title", ""),
        "description":       root.findtext("description", ""),
        "version":           root.findtext("version", ""),
        "release_info":      status_date or root.findtext("release-info", ""),
        "publisher":         status_text or root.findtext("publisher", ""),
    }

    benchmark = STIGBenchmark(bench_data)

    for group_elem in root.findall("Group"):
        rule_obj = parse_group_element(group_elem)
        if rule_obj:
            benchmark.rules.append(rule_obj)

    return benchmark


def parse_group_element(group_elem):
    """Helper to parse a single Group XML element into a STIGRule object."""
    group_id    = group_elem.attrib.get("id", "")
    group_title = (group_elem.findtext("title", "") or "").strip()
    group_desc  = (group_elem.findtext("description", "") or "").strip()

    rule_elem = group_elem.find("Rule")
    if rule_elem is None:
        return None

    rule_id  = rule_elem.attrib.get("id", "")
    stig_id  = (rule_elem.findtext("version", "") or "").strip()
    severity = rule_elem.attrib.get("severity", "medium")
    title    = (rule_elem.findtext("title", "") or "").strip()

    # Description appears in two formats depending on the authoring tool:
    #   A) Actual XML subelement: <description><VulnDiscussion>...</VulnDiscussion></description>
    #      findtext() only returns text before the first child, so we must use find().
    #   B) Escaped/CDATA text: <description>&lt;VulnDiscussion&gt;...&lt;/VulnDiscussion&gt;</description>
    #      ElementTree normalises both entity-refs and CDATA to plain text in .text.
    vuln_discussion = ""
    desc_el = rule_elem.find("description")
    if desc_el is not None:
        vuln_el = desc_el.find("VulnDiscussion")
        if vuln_el is not None:
            vuln_discussion = (vuln_el.text or "").strip()
        else:
            raw_desc = (desc_el.text or "").strip()
            if "<VulnDiscussion>" in raw_desc:
                m = re.search(r"<VulnDiscussion>(.*?)</VulnDiscussion>", raw_desc, re.DOTALL)
                vuln_discussion = m.group(1).strip() if m else raw_desc
            else:
                vuln_discussion = raw_desc

    rationale = (rule_elem.findtext("rationale", "") or "").strip()

    # Collect all NIST reference elements (one per line).
    # Each reference may contain multiple lines with leading whitespace — normalise each line.
    nist_values = []
    for ref in rule_elem.findall("reference"):
        if ref.text:
            lines = [l.strip() for l in ref.text.splitlines() if l.strip()]
            if lines:
                nist_values.extend(lines)
    nist_control = "\n".join(nist_values)

    # Collect all CCI ident values (one per line)
    cci_values = []
    for ident in rule_elem.findall("ident"):
        sys_attr = ident.attrib.get("system", "")
        if sys_attr.endswith("/cci") or sys_attr == "http://cyber.mil/cci":
            if ident.text:
                cci_values.append(ident.text.strip())
    if not cci_values:
        ident_el = rule_elem.find("ident")
        if ident_el is not None and ident_el.text:
            cci_values.append(ident_el.text.strip())
    cci = "\n".join(cci_values)

    fix_text = (rule_elem.findtext("fixtext", "") or "").strip()

    manual_check = ""
    check_elem = rule_elem.find("check")
    if check_elem is not None:
        manual_check = (check_elem.findtext("check-content", "") or "").strip()

    custom_fields = {}
    for custom_el in rule_elem.findall("custom-attribute"):
        name = custom_el.attrib.get("name")
        if name:
            custom_fields[name] = custom_el.text or ""

    return STIGRule({
        "group_id":          group_id,
        "group_title":       group_title,
        "group_description": group_desc,
        "rule_id":           rule_id,
        "stig_id":           stig_id,
        "severity":          severity,
        "title":             title,
        "vuln_discussion":   vuln_discussion,
        "nist_control":      nist_control,
        "cci":               cci,
        "rationale":         rationale,
        "manual_check":      manual_check,
        "fix_text":          fix_text,
        "custom_fields":     custom_fields,
    })


def generate_benchmark_xml(benchmark):
    """Generates an XCCDF 1.1 XML string in the layout DISA STIGs use."""
    bid = benchmark.benchmark_id or DEFAULT_BENCHMARK_ID
    prefix = _id_prefix(bid)
    check_system = f"urn:xccdf:C-{_product_slug(prefix)}:manual"

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '',
        '<Benchmark',
        '    xmlns="http://checklists.nist.gov/xccdf/1.1"',
        '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"',
        '    xmlns:dc="http://purl.org/dc/elements/1.1/"',
        '    xmlns:cpe="http://cpe.mitre.org/language/2.0"',
        '    xmlns:html="http://www.w3.org/1999/xhtml"',
        '    xmlns:dsig="http://www.w3.org/2000/09/xmldsig#"',
        f'    id="{_attr(bid)}"',
        '    resolved="false"',
        '    xml:lang="en"',
        '    xsi:schemaLocation="http://checklists.nist.gov/xccdf/1.1 http://checklists.nist.gov/xccdf/1.1/xccdf-1.1-schema.xsd">',
        '',
        f'  <status date="{_attr(benchmark.release_info)}">{_xe(benchmark.publisher)}</status>',
        '',
        f'  <title>{_xe(benchmark.title)}</title>',
        '',
        f'  <description>{_xe(benchmark.description)}</description>',
        '',
        f'  <version>{_xe(benchmark.version)}</version>',
        '',
    ]

    for idx, rule in enumerate(benchmark.rules):
        group_id = rule.group_id or f"{prefix}_group_{idx + 1:04d}"
        rule_id  = rule.rule_id  or f"{prefix}_rule_{idx + 1:04d}"
        severity = rule.severity or "medium"

        # VulnDiscussion comes from the form. The other sub-elements are the
        # placeholders the public XCCDF/STIG convention expects in every rule
        # description; they are written empty so nothing is assumed for the reader.
        desc_inner = "\n".join(
            [f"        <VulnDiscussion>{_cdata_safe(rule.vuln_discussion)}</VulnDiscussion>"]
            + [f"        <{tag}></{tag}>" for tag in DESCRIPTION_PLACEHOLDERS]
        )

        lines += [
            f'  <Group id="{_attr(group_id)}" xml:lang="en">',
            f'    <title>{_xe(rule.group_title)}</title>',
            f'    <description>{_xe(rule.group_description)}</description>',
            '',
            f'    <Rule id="{_attr(rule_id)}"',
            f'          severity="{_attr(severity)}"',
            '          weight="10.0">',
            '',
            f'      <version>{_xe(rule.stig_id or benchmark.version)}</version>',
            '',
            f'      <title>{_xe(rule.title)}</title>',
            '',
            '      <description><![CDATA[',
            desc_inner,
            '      ]]></description>',
            '',
        ]

        nist_entries = [v.strip() for v in re.split(r'[\n,]+', rule.nist_control or '') if v.strip()]
        if nist_entries:
            lines.append('      <reference href="https://csrc.nist.gov/projects/risk-management-framework">')
            for nc in nist_entries:
                lines.append(f'        {_xe(nc)}')
            lines += ['      </reference>', '']

        cci_entries = [v.strip() for v in re.split(r'[\n,]+', rule.cci or '') if v.strip()]
        if cci_entries:
            for cci_val in cci_entries:
                lines.append(f'      <ident system="http://cyber.mil/cci">{_xe(cci_val)}</ident>')
            lines.append('')

        if rule.rationale:
            lines += [
                f'      <rationale>{_xe(rule.rationale)}</rationale>',
                '',
            ]

        lines += [
            f'      <check system="{_attr(check_system)}">',
            '        <check-content>',
            '  <![CDATA[',
            _cdata_safe(rule.manual_check),
            '  ]]>',
            '        </check-content>',
            '      </check>',
            '',
            f'      <fixtext fixref="fix_{_attr(rule_id)}">',
            '  <![CDATA[',
            _cdata_safe(rule.fix_text),
            '  ]]>',
            '      </fixtext>',
            '',
        ]

        if rule.custom_fields:
            for k, v in rule.custom_fields.items():
                lines.append(f'      <custom-attribute name="{_attr(k)}">{_xe(v)}</custom-attribute>')
            lines.append('')

        lines += [
            '    </Rule>',
            '  </Group>',
            '',
        ]

    lines.append('</Benchmark>')
    return '\n'.join(lines)


def generate_xml(rule_obj):
    """Wrapper to support existing code paths working with a single rule."""
    bench = STIGBenchmark({
        "benchmark_id": f"Benchmark_for_rule_{rule_obj.rule_id}",
        "title":        f"Single Rule Benchmark: {rule_obj.title}",
        "rules":        [rule_obj],
    })
    filename = f"rule_{rule_obj.rule_id}.xml"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(generate_benchmark_xml(bench))
    return filename
