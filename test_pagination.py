#!/usr/bin/env python3
"""
Test Pagination System
"""

KEYS_PER_PAGE = 8

def paginate_list(items, page=1, per_page=KEYS_PER_PAGE):
    """Paginate a list of items"""
    total_items = len(items)
    total_pages = (total_items + per_page - 1) // per_page
    
    if page < 1:
        page = 1
    if page > total_pages and total_pages > 0:
        page = total_pages
    
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    
    return {
        'items': items[start_idx:end_idx],
        'page': page,
        'total_pages': total_pages,
        'total_items': total_items,
        'has_next': page < total_pages,
        'has_prev': page > 1
    }

# Test with different scenarios
print("=" * 60)
print("Testing Pagination System")
print("=" * 60)
print()

# Test 1: 37 keys (5 pages)
print("Test 1: 37 keys")
keys = [f"KEY-{i:03d}" for i in range(1, 38)]
for page in range(1, 6):
    result = paginate_list(keys, page)
    print(f"  Page {result['page']}/{result['total_pages']}: {len(result['items'])} keys")
    print(f"    Has prev: {result['has_prev']}, Has next: {result['has_next']}")
    print(f"    Keys: {result['items'][:3]}...")
print()

# Test 2: 8 keys (1 page)
print("Test 2: 8 keys (exactly 1 page)")
keys = [f"KEY-{i:03d}" for i in range(1, 9)]
result = paginate_list(keys, 1)
print(f"  Page {result['page']}/{result['total_pages']}: {len(result['items'])} keys")
print(f"    Has prev: {result['has_prev']}, Has next: {result['has_next']}")
print()

# Test 3: 3 keys (less than 1 page)
print("Test 3: 3 keys (less than 1 page)")
keys = [f"KEY-{i:03d}" for i in range(1, 4)]
result = paginate_list(keys, 1)
print(f"  Page {result['page']}/{result['total_pages']}: {len(result['items'])} keys")
print(f"    Has prev: {result['has_prev']}, Has next: {result['has_next']}")
print()

# Test 4: 100 keys (13 pages)
print("Test 4: 100 keys")
keys = [f"KEY-{i:03d}" for i in range(1, 101)]
result = paginate_list(keys, 1)
print(f"  Total pages: {result['total_pages']}")
result = paginate_list(keys, 13)
print(f"  Last page ({result['page']}): {len(result['items'])} keys")
print()

# Test 5: Edge cases
print("Test 5: Edge cases")
keys = [f"KEY-{i:03d}" for i in range(1, 38)]
print(f"  Page 0 (should become 1): {paginate_list(keys, 0)['page']}")
print(f"  Page 999 (should become last): {paginate_list(keys, 999)['page']}")
print(f"  Page -5 (should become 1): {paginate_list(keys, -5)['page']}")
print()

print("=" * 60)
print("✅ All tests completed!")
print("=" * 60)
