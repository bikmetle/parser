import requests

url = "https://hackerone.com/graphql"

headers = {
    "Host": "hackerone.com",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:134.0) Gecko/20100101 Firefox/134.0",
    "Accept": "*/*",
    "Accept-Language": "ru,en-US;q=0.7,en;q=0.3",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://hackerone.com/directory/programs?offers_bounties=true&order_direction=DESC&order_field=launched_at",
    "Content-Type": "application/json",
    "Origin": "https://hackerone.com",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Priority": "u=4",
    "TE": "trailers",
}

# JSON payload from the JSON
payload = {
    "operationName": "DirectoryQuery",
    "variables": {
        "where": {
            "_and": [
                {
                    "_or": [
                        {"offers_bounties": {"_eq": True}},
                        {"external_program": {"offers_rewards": {"_eq": True}}},
                    ]
                },
                {
                    "_or": [
                        {"submission_state": {"_eq": "open"}},
                        {"submission_state": {"_eq": "api_only"}},
                        {"external_program": {}},
                    ]
                },
                {"_not": {"external_program": {}}},
                {
                    "_or": [
                        {
                            "_and": [
                                {"state": {"_neq": "sandboxed"}},
                                {"state": {"_neq": "soft_launched"}},
                            ]
                        },
                        {"external_program": {}},
                    ]
                },
            ]
        },
        "first": 25,
        "secureOrderBy": {"launched_at": {"_direction": "DESC"}},
        "product_area": "directory",
        "product_feature": "programs",
    },
    "query": """query DirectoryQuery($cursor: String, $secureOrderBy: FiltersTeamFilterOrder, $where: FiltersTeamFilterInput) {
  me {
    id
    edit_unclaimed_profiles
    __typename
  }
  teams(first: 25, after: $cursor, secure_order_by: $secureOrderBy, where: $where) {
    pageInfo {
      endCursor
      hasNextPage
      __typename
    }
    edges {
      node {
        id
        bookmarked
        ...TeamTableResolvedReports
        ...TeamTableAvatarAndTitle
        ...TeamTableLaunchDate
        ...TeamTableMinimumBounty
        ...TeamTableAverageBounty
        ...BookmarkTeam
        __typename
      }
      __typename
    }
    __typename
  }
}

fragment TeamTableResolvedReports on Team {
  id
  resolved_report_count
  __typename
}

fragment TeamTableAvatarAndTitle on Team {
  id
  profile_picture(size: medium)
  name
  handle
  submission_state
  triage_active
  publicly_visible_retesting
  state
  allows_bounty_splitting
  external_program {
    id
    __typename
  }
  ...TeamLinkWithMiniProfile
  __typename
}

fragment TeamLinkWithMiniProfile on Team {
  id
  handle
  name
  __typename
}

fragment TeamTableLaunchDate on Team {
  id
  launched_at
  __typename
}

fragment TeamTableMinimumBounty on Team {
  id
  currency
  base_bounty
  __typename
}

fragment TeamTableAverageBounty on Team {
  id
  currency
  average_bounty_lower_amount
  average_bounty_upper_amount
  __typename
}

fragment BookmarkTeam on Team {
  id
  bookmarked
  __typename
}""",
}

# Make the POST request
response = requests.post(url, headers=headers, json=payload)

# Print the response
print(response.status_code)
print(response.json())  # Assuming the response is JSON