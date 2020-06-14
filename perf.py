def test():
    """Stupid test function"""
    L = [i for i in range(100)]


# want to test two different variants
# fl-string
# vs compositing with %
# this is only an indirect test
# also to validate the logging codepath!

if __name__ == '__main__':
    import timeit
    print(timeit.timeit("test()", setup="from __main__ import test"))
