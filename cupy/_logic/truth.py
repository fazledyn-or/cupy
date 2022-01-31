import cupy
from cupy._core import _routines_logic as _logic
from cupy._core import _fusion_thread_local
from cupy import _util


def all(a, axis=None, out=None, keepdims=False):
    """Tests whether all array elements along a given axis evaluate to True.

    Parameters
    ----------
    a : cupy.ndarray)
        Input array.
    axis : int or tuple of ints)
        Along which axis to compute all.
        The flattened array is used by default.
    out : cupy.ndarray
        Output array.
    keepdims : bool
        If ``True``, the axis is remained as an axis of size one.

    Returns
    -------
    y : cupy.ndarray
        An array reduced of the input array along the axis.

    See Also
    --------
    numpy.all

    """
    if _fusion_thread_local.is_fusing():
        if keepdims:
            raise NotImplementedError(
                'cupy.all does not support `keepdims` in fusion yet.')
        return _fusion_thread_local.call_reduction(
            _logic.all, a, axis=axis, out=out)

    _util.check_array(a, arg_name='a')

    return a.all(axis=axis, out=out, keepdims=keepdims)


def any(a, axis=None, out=None, keepdims=False):
    """Tests whether any array elements along a given axis evaluate to True.

    Parameters
    ----------
    a : cupy.ndarray
        Input array.
    axis : int or tuple of ints
        Along which axis to compute all.
        The flattened array is used by default.
    out : cupy.ndarray
        Output array.
    keepdims : bool
        If ``True``, the axis is remained as an axis of size one.

    Returns
    -------
    y : cupy.ndarray
        An array reduced of the input array along the axis.

    See Also
    --------
    numpy.any

    """
    if _fusion_thread_local.is_fusing():
        if keepdims:
            raise NotImplementedError(
                'cupy.any does not support `keepdims` in fusion yet.')
        return _fusion_thread_local.call_reduction(
            _logic.any, a, axis=axis, out=out)

    _util.check_array(a, arg_name='a')

    return a.any(axis=axis, out=out, keepdims=keepdims)


def in1d(ar1, ar2, assume_unique=False, invert=False):
    """Tests whether each element of a 1-D array is also present in a second
    array.

    Returns a boolean array the same length as ``ar1`` that is ``True``
    where an element of ``ar1`` is in ``ar2`` and ``False`` otherwise.

    Parameters
    ----------
    ar1 : cupy.ndarray
        Input array.
    ar2 : cupy.ndarray
        The values against which to test each value of ``ar1``.
    assume_unique : bool, optional
        Ignored
    invert : bool, optional
        If ``True``, the values in the returned array
        are inverted (that is, ``False`` where an element of ``ar1`` is in
        ``ar2`` and ``True`` otherwise). Default is ``False``.

    Returns
    -------
    y : cupy.ndarray, bool
        The values ``ar1[in1d]`` are in ``ar2``.

    """
    # Ravel both arrays, behavior for the first array could be different
    ar1 = ar1.ravel()
    ar2 = ar2.ravel()
    if ar1.size == 0 or ar2.size == 0:
        if invert:
            return cupy.ones(ar1.shape, dtype=cupy.bool_)
        else:
            return cupy.zeros(ar1.shape, dtype=cupy.bool_)
    # Use brilliant searchsorted trick
    # https://github.com/cupy/cupy/pull/4018#discussion_r495790724
    ar2 = cupy.sort(ar2)
    v1 = cupy.searchsorted(ar2, ar1, 'left')
    v2 = cupy.searchsorted(ar2, ar1, 'right')
    return v1 == v2 if invert else v1 != v2


def intersect1d(arr1, arr2, assume_unique=False, return_indices=False):
    """Find the intersection of two arrays.
    Returns the sorted, unique values that are in both of the input arrays.

    Parameters
    ----------
    arr1, arr2 : cupy.ndarray
        Input arrays. Arrays will be flattened if they are not in 1D.
    assume_unique : bool
        By default, None. If set True, the input arrays will be
        assumend to be unique, which speeds up the calculation. If set True,
        but the arrays are not unique, incorrect results and out-of-bounds
        indices could result.
    return_indices : bool
       By default, False. If True, the indices which correspond to the
       intersection of the two arrays are returned.

    Returns
    -------
    intersect1d : cupy.ndarray
        Sorted 1D array of common and unique elements.
    comm1 : cupy.ndarray
        The indices of the first occurrences of the common values
        in `arr1`. Only provided if `return_indices` is True.
    comm2 : cupy.ndarray
        The indices of the first occurrences of the common values
        in `arr2`. Only provided if `return_indices` is True.

    See Also
    --------
    numpy.intersect1d

    """
    if not assume_unique:
        if return_indices:
            arr1, ind1 = cupy.unique(arr1, return_index=True)
            arr2, ind2 = cupy.unique(arr2, return_index=True)
        else:
            arr1 = cupy.unique(arr1)
            arr2 = cupy.unique(arr2)
    else:
        arr1 = arr1.ravel()
        arr2 = arr2.ravel()

    aux = cupy.concatenate((arr1, arr2))
    if return_indices:
        aux_sort_indices = cupy.argsort(aux)
        aux = aux[aux_sort_indices]
    else:
        aux.sort()

    mask = aux[1:] == aux[:-1]
    int1d = aux[:-1][mask]

    if return_indices:
        arr1_indices = aux_sort_indices[:-1][mask]
        arr2_indices = aux_sort_indices[1:][mask] - arr1.size
        if not assume_unique:
            arr1_indices = ind1[arr1_indices]
            arr2_indices = ind2[arr2_indices]

        return int1d, arr1_indices, arr2_indices
    else:
        return int1d


def isin(element, test_elements, assume_unique=False, invert=False):
    """Calculates element in ``test_elements``, broadcasting over ``element``
    only. Returns a boolean array of the same shape as ``element`` that is
    ``True`` where an element of ``element`` is in ``test_elements`` and
    ``False`` otherwise.

    Parameters
    ----------
    element : cupy.ndarray
        Input array.
    test_elements : cupy.ndarray
        The values against which to test each
        value of ``element``. This argument is flattened if it is an
        array or array_like.
    assume_unique : bool, optional
        Ignored
    invert : bool, optional
        If ``True``, the values in the returned array
        are inverted, as if calculating element not in ``test_elements``.
        Default is ``False``.

    Returns
    -------
    y : cupy.ndarray, bool
        Has the same shape as ``element``. The values ``element[isin]``
        are in ``test_elements``.

    """
    return in1d(element, test_elements, assume_unique=assume_unique,
                invert=invert).reshape(element.shape)


def union1d(arr1, arr2):
    """Find the union of two arrays.

    Returns the unique, sorted array of values that are in either of
    the two input arrays.

    Parameters
    ----------
    arr1, arr2 : cupy.ndarray
        Input arrays. They are flattend if they are not already 1-D.

    Returns
    -------
    union1d : cupy.ndarray
        Sorted union of the input arrays.

    See Also
    --------
    numpy.union1d

    """
    return cupy.unique(cupy.concatenate((arr1, arr2), axis=None))
