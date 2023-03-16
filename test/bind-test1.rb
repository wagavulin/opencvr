#!/usr/bin/env ruby

$:.unshift(File.dirname(__FILE__) + "/..")
require 'numo/narray'
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
    assert_equal(CV2.bindTest3(1), 1+1)
  end

  def test_bindTest4_1
    assert_equal(CV2.bindTest4(2, [10, 11]), [12, 9])
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

  def test_bindTest_double
    assert_equal(CV2.bindTest_double(2.0), 2.5)
    assert_equal(CV2.bindTest_double(2), 2.5)
  end

  def test_bind_overload
    assert_equal(CV2.bindTest_overload(3.0), 6.0)
    assert_equal(CV2.bindTest_overload([10, 20]), 60)
    assert_equal(CV2.bindTest_overload(3.0, 3), 9.0)
  #   ret = CV2.bindTest_overload([1, 2], [3, 4], 5)
  #   assert_equal(ret, 15)
  #   ret = CV2.bindTest_overload([[1, 2], [3, 4], 5])
  #   assert_equal(ret, 15)
  end

  # def test_bind_overload2
  #   assert_equal(CV2.bindTest_overload2(10), 11)
  #   assert_equal(CV2.bindTest_overload2(10, 20), 30)
  # end

  # def test_bind_Mat
  #   m1 = CV2.imread(__dir__ + "/images/200x200bgrw.png")
  #   assert_equal(m1.at(0, 0), [255, 0, 0])
  #   m2 = CV2.bindTest_InOut_Mat(m1)
  #   assert_equal(m1.at(0, 0), [100, 110, 120])
  #   assert_equal(m2.at(0, 0), [100, 110, 120])
  # end

  def test_bind_primitive_types
    assert_equal(CV2.bindTest_InOut_bool(true), false)
  #   ret = CV2.bindTest_InOut_uchar(10)
  #   assert_equal(ret, 20)
  #   ret = CV2.bindTest_InOut_int(10)
  #   assert_equal(ret, 20)
    assert_equal(CV2.bindTest_Out_intp(), 10)
    assert_equal(CV2.bindTest_InOut_size_t(10), 20)
    assert_equal(CV2.bindTest_InOut_float(1.0), 1.5)
    assert_equal(CV2.bindTest_InOut_float(1), 1.5) # float arg should also accept int
    assert_equal(CV2.bindTest_InOut_double(1.0), 2.5)
    assert_equal(CV2.bindTest_InOut_double(1), 2.5)
    assert_equal(CV2.bindTest_Out_doublep(), 2.5)
  end

  def test_bind_basic_classes
    assert_equal(CV2.bindTest_In_String("hello"), 5)
    assert_equal(CV2.bindTest_InOut_Scalar([10, 20, 30, 40]), [11, 22, 33, 44])
    assert_equal(CV2.bindTest_InOut_Size([100, 200]) ,[110, 210])
    assert_equal(CV2.bindTest_InOut_Size2i([100000000, 200000000]) ,[100000020, 200000020])
    #assert_equal(CV2.bindTest_InOut_Size2l([10000000000, 20000000000]) ,[10000000020, 20000000020])
    assert_equal(CV2.bindTest_InOut_Size2f([20.5, 21.5]), [21.0, 22.0])
    assert_equal(CV2.bindTest_InOut_Size2f([20, 21]), [20.5, 21.5]) # Size2f arg should also accept int
    assert_equal(CV2.bindTest_Out_Point(100), [110, 90])
    assert_equal(CV2.bindTest_Out_Pointp(100), [111, 89])
    assert_equal(CV2.bindTest_InOut_Point([100, 200]), [110, 210])
    assert_equal(CV2.bindTest_InOut_Point2f([10.0, 11.0]), [10.5, 11.5])
    assert_equal(CV2.bindTest_InOut_Point2f([10, 11]), [10.5, 11.5]) # Point2f arg should also accept Point2i
    assert_equal(CV2.bindTest_Out_Point2fp(), [0.5, 1.5])
    assert_equal(CV2.bindTest_InOut_Rect([100, 110, 120, 130]), [110, 130, 150, 170])
    assert_equal(CV2.bindTest_Out_Rectp(), [10, 20, 30, 40])
    assert_equal(CV2.bindTest_InOut_RotatedRect([[100, 200], [10, 20], 30]), [[100.5, 200.5], [10.5, 20.5], 30.5])
    assert_equal(CV2.bindTest_InOut_vector_int([10, 20, 30]), [13, 23, 33])
    assert_equal(CV2.bindTest_InOut_vector_Point([[1, 2], [3, 4]]), [[2, 3], [4, 5], [10, 11], [20, 21]])
    assert_equal(CV2.bindTest_InOut_vector_Rect([[10,20,30,40], [50,60,70,80]]), [[11,22,33,44], [51,62,73,84]])
  end

  def test_mat_1
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
  end

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
    assert_equal(foo.method2(10, 1), 134)
    # constructor with argument
    foo = CV2::Foo.new(234)
    assert_equal(foo.method1(1), 235)
    # static method (as class method)
    assert_equal(CV2::Foo::smethod1(10), 20)
    assert_equal(CV2::Foo.smethod1(10), 20)
    # static method (as global function)
    assert_equal(CV2::Foo_smethod1(10), 20)
    assert_equal(CV2.Foo_smethod1(10), 20)
    # static method in subsubmodule
    assert_equal(CV2::Ns1::Ns11::SubSubC1::smethod1(10), 30)
    assert_equal(CV2::Ns1::Ns11::SubSubC1.smethod1(10), 30)
    assert_equal(CV2::Ns1::Ns11::SubSubC1_smethod1(10), 30)
    assert_equal(CV2::Ns1::Ns11.SubSubC1_smethod1(10), 30)
  end

  def test_submodule
    # class in submodule
    subsubc1 = CV2::Ns1::Ns11::SubSubC1.new()
    assert_equal(subsubc1.method1(10), 121)
    # function in subsubmodule
    assert_equal(CV2::Ns1::Ns11::bindTest_Ns11(10), 21)
  end

  def test_class_ex
    ssc1 = CV2::Ns1::Ns11::SubSubC1.new(222)
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

  def test_imgproc
    img0 = Numo::UInt8.zeros(600, 800, 3)
    img0[0..-1, 0..-1, 0] = 255
    img1 = img0.clone()
    CV2::rectangle(img1, [50,50], [150, 100], [255,255,255])
    assert_not_equal(img1, img0)
    #CV2::imshow("Test", img0); CV2::waitKey(0); CV2::destroyAllWindows()
  end
end
