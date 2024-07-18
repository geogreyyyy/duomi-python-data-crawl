def paginate_5000(total,N):
    if N <= 0:
        raise ValueError("N必须大于0")
    pages_per_range = total // N
    remainder = total % N
    ranges = []
    start = 1
    for i in range(N):
        if i == N - 1:
            end = start + pages_per_range + remainder - 1
        else:
            end = start + pages_per_range - 1
        ranges.append((start, end))
        start = end + 1
    return ranges
N = 5
total = 4980
ranges = paginate_5000(total,N)

for range_ in ranges:
    print(f"第{ranges.index(range_)+1}份：{range_[0]}-{range_[1]}")