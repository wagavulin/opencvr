#!/usr/bin/env ruby

$:.unshift(File.dirname(__FILE__) + "/..")
require 'cv2'
require 'test/unit'

class BindTest < Test::Unit::TestCase
  def test_bindTest1_1
    ret = CV2.bindTest1(1, [10, 11])
    assert_equal(ret[0], 1+10+11+23+10+1.2)
    assert_equal(ret[1], [20, 1])
    assert_equal(ret[2], 23)
  end

  def test_bindTest1_2
    ret = CV2.bindTest1(1, [10, 11], 100, e: 1000)
    assert_equal(ret[0], 1+10+11+23+100+1000)
    assert_equal(ret[1], [20, 1])
    assert_equal(ret[2], 23)
  end

  def test_bindTest1_3
    ret = CV2.bindTest1(1, [10, 11], e: 1000, d: 100)
    assert_equal(ret[0], 1+10+11+23+100+1000)
    assert_equal(ret[1], [20, 1])
    assert_equal(ret[2], 23)
  end

  def test_bindTest2_1
    CV2.bindTest2(1)
  end

  def test_bindTest3_1
    ret = CV2.bindTest3(1)
    assert_equal(ret, 1+1)
  end

  def test_bindTest4_1
    ret = CV2.bindTest4(2, [10, 11])
    assert_equal(ret[0], 12)
    assert_equal(ret[1], 9)
  end

  def test_bindTest5_1
    ret = CV2.bindTest5(2, [10, 11])
    assert_equal(ret[0][0], 12)
    assert_equal(ret[0][1], 9)
    assert_equal(ret[1], 23)
  end

  def test_bindTest6_1
    ret = CV2.bindTest6(2, [10, 11])
    assert_equal(ret[0], true)
    assert_equal(ret[1][0], 12)
    assert_equal(ret[1][1], 9)
    assert_equal(ret[2], 23)
  end
end
