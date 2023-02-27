#!/usr/bin/env ruby

$:.unshift(File.dirname(__FILE__) + "/..")
require 'cv2'
require 'test/unit'

class BindTest < Test::Unit::TestCase
  # def test_bindTest1_1
  #   ret = CV2.bindTest1(1, [10, 11])
  #   assert_equal(ret[0], 1+10+11+23+10+1.2)
  #   assert_equal(ret[1], [20, 1])
  #   assert_equal(ret[2], 23)
  # end

  # def test_bindTest1_2
  #   ret = CV2.bindTest1(1, [10, 11], 100, e: 1000)
  #   assert_equal(ret[0], 1+10+11+23+100+1000)
  #   assert_equal(ret[1], [20, 1])
  #   assert_equal(ret[2], 23)
  # end

  # def test_bindTest1_3
  #   ret = CV2.bindTest1(1, [10, 11], e: 1000, d: 100)
  #   assert_equal(ret[0], 1+10+11+23+100+1000)
  #   assert_equal(ret[1], [20, 1])
  #   assert_equal(ret[2], 23)
  # end

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

  # def test_bindTest5_1
  #   ret = CV2.bindTest5(2, [10, 11])
  #   assert_equal(ret[0][0], 12)
  #   assert_equal(ret[0][1], 9)
  #   assert_equal(ret[1], 23)
  # end

  # def test_bindTest6_1
  #   ret = CV2.bindTest6(2, [10, 11])
  #   assert_equal(ret[0], true)
  #   assert_equal(ret[1][0], 12)
  #   assert_equal(ret[1][1], 9)
  #   assert_equal(ret[2], 23)
  # end

  # def test_bind_overload
  #   ret = CV2.bindTest_overload([1, 2], [3, 4], 5)
  #   assert_equal(ret, 15)
  #   ret = CV2.bindTest_overload([[1, 2], [3, 4], 5])
  #   assert_equal(ret, 15)
  # end

  # def test_bind_Mat
  #   m1 = CV2.imread(__dir__ + "/images/200x200bgrw.png")
  #   assert_equal(m1.at(0, 0), [255, 0, 0])
  #   m2 = CV2.bindTest_InOut_Mat(m1)
  #   assert_equal(m1.at(0, 0), [100, 110, 120])
  #   assert_equal(m2.at(0, 0), [100, 110, 120])
  # end

  # def test_bind_primitive_types
  #   ret = CV2.bindTest_InOut_bool(true)
  #   assert_equal(ret, false)
  #   ret = CV2.bindTest_InOut_uchar(10)
  #   assert_equal(ret, 20)
  #   ret = CV2.bindTest_InOut_int(10)
  #   assert_equal(ret, 20)
  #   ret = CV2.bindTest_Out_intp()
  #   assert_equal(ret, 10)
  #   ret = CV2.bindTest_InOut_size_t(10)
  #   assert_equal(ret, 20)
  #   ret = CV2.bindTest_InOut_float(1)
  #   assert_equal(ret, 1.5)
  #   ret = CV2.bindTest_InOut_double(1)
  #   assert_equal(ret, 1.5)
  # end

  def test_bind_basic_classes
  #   ret = CV2.bindTest_InOut_Size([100, 200])
  #   assert_equal(ret, [110, 210])
  #   ret = CV2.bindTest_InOut_Size2f([20.5, 21.5])
  #   assert_equal(ret, [21.0, 22.0])
  #   ret = CV2.bindTest_InOut_Size2f([20, 21])
  #   assert_equal(ret, [20.5, 21.5])
    ret = CV2.bindTest_Out_Point(100)
    assert_equal(ret, [110, 90])
    ret = CV2.bindTest_InOut_Point([100, 200])
    assert_equal(ret, [110, 210])
  #   ret = CV2.bindTest_InOut_Point2f([10.5, 11.5])
  #   assert_equal(ret, [11.0, 12.0])
  #   ret = CV2.bindTest_InOut_Point2f([10, 11])
  #   assert_equal(ret, [10.5, 11.5])
  #   ret = CV2.bindTest_InOut_RotatedRect([[100, 200], [10, 20], 30])
  #   assert_equal(ret, [[100.5, 200.5], [10.5, 20.5], 30.5])
  #   ret = CV2.bindTest_InOut_vector_Point([[1, 2], [3, 4]])
  #   assert_equal(ret, [[2, 3], [4, 5], [10, 11], [20, 21]])
  end

  # def test_mat_1
  #   m1 = CV2.imread(__dir__ + "/images/200x200bgrw.png")
  #   c = m1.at(50, 50)
  #   assert_equal(c[0], 255)
  #   assert_equal(c[1], 0)
  #   assert_equal(c[2], 0)
  #   c = m1.at(50, 150)
  #   assert_equal(c[0], 0)
  #   assert_equal(c[1], 255)
  #   assert_equal(c[2], 0)
  #   c = m1.at(150, 50)
  #   assert_equal(c[0], 0)
  #   assert_equal(c[1], 0)
  #   assert_equal(c[2], 255)
  #   c = m1.at(150, 150)
  #   assert_equal(c[0], 255)
  #   assert_equal(c[1], 255)
  #   assert_equal(c[2], 255)
  # end

  # def test_mat_at
  #   m1 = CV2.imread(__dir__ + "/images/alpha.png", CV2::IMREAD_GRAYSCALE)
  #   assert_equal(m1.channels, 1)
  #   assert_equal(m1.at(0, 0), 255)
  #   m3 = CV2.imread(__dir__ + "/images/alpha.png", CV2::IMREAD_COLOR)
  #   assert_equal(m3.channels, 3)
  #   assert_equal(m3.at(0, 0), [255, 255, 255])
  #   m4 = CV2.imread(__dir__ + "/images/alpha.png", CV2::IMREAD_UNCHANGED)
  #   assert_equal(m4.channels, 4)
  #   assert_equal(m4.at(0, 0), [255, 255, 255, 64])
  # end

  def test_class_instance_methods
    # instance method
    foo = CV2::Foo.new()
    assert_equal(foo.method1(10), 133)
    # overloaded instance method
    #assert_equal(foo.method2(10), 134)
    #foo.method2(10, 2)
    # static method
    #assert_equal(CV2::Foo::smethod1(10), 20)
  end

  def test_submodule
    # class in submodule
    subsubc1 = CV2::Ns1::Ns11::SubSubC1.new()
    assert_equal(subsubc1.method1(10), 121)
    # function in subsubmodule
    assert_equal(CV2::Ns1::Ns11::bindTest_Ns11(10), 21)
  end

  def test_enum
    # enum under CV2
    assert_equal(CV2::MYENUM1_COLOR, 1)
    # old style enum under submodule
    assert_equal(CV2::Ns1::MYENUM2_VALUE_C, 10)
    # scoped enum under submodule
    assert_equal(CV2::Ns1::MyEnum3_MYENUM3_VALUE_R, 120)
    # old style enum under subsubmodule
    assert_equal(CV2::Ns1::Ns11::MYENUM4_VALUE_1, 1000)
  end
end
