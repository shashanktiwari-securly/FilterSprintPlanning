import json, sys, os

AGENT_DIR = '/home/ubuntu/.cursor/projects/workspace/agent-tools/'
DATA_DIR = '/workspace/all-products-analysis/data/'

def norm(issue):
    f = issue.get('fields', {})
    sp = None
    for k in ('customfield_10005', 'customfield_11247'):
        v = f.get(k)
        if isinstance(v, (int, float)):
            sp = float(v); break
    sprints = []
    for s in (f.get('customfield_10007') or []):
        if isinstance(s, dict) and s.get('id') is not None:
            sprints.append({
                'id': s.get('id'), 'name': s.get('name'), 'state': (s.get('state') or '').lower(),
                'boardId': s.get('boardId'), 'startDate': s.get('startDate'),
                'endDate': s.get('endDate'), 'completeDate': s.get('completeDate'),
            })
    return {
        'key': issue.get('key'),
        'project': (f.get('project') or {}).get('key'),
        'issuetype': (f.get('issuetype') or {}).get('name'),
        'status': (f.get('status') or {}).get('name'),
        'statusCategory': ((f.get('status') or {}).get('statusCategory') or {}).get('key'),
        'created': (f.get('created') or '')[:10] or None,
        'resolved': (f.get('resolutiondate') or '')[:10] or None,
        'storyPoints': sp,
        'sprints': sprints,
    }

def ingest(project, fileid, append):
    path = AGENT_DIR + fileid + '.txt'
    data = json.load(open(path))
    issues = data.get('issues', [])
    mode = 'a' if append else 'w'
    with open(DATA_DIR + project + '.jsonl', mode) as out:
        for iss in issues:
            out.write(json.dumps(norm(iss)) + '\n')
    return len(issues), data.get('isLast', True), data.get('nextPageToken')

if __name__ == '__main__':
    # args: project fileid append(0/1)
    project, fileid, append = sys.argv[1], sys.argv[2], sys.argv[3] == '1'
    n, is_last, token = ingest(project, fileid, append)
    print(json.dumps({'project': project, 'added': n, 'isLast': is_last, 'token': token}))
