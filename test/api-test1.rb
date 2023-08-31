#!/usr/bin/env ruby

$:.unshift(File.dirname(__FILE__) + "/..")
require 'fileutils'
require 'numo/narray'
require 'cv2'
require 'test/unit'

class ApiTest < Test::Unit::TestCase
  def setup
    @script_dir = File.dirname(__FILE__)
    @in_dir = "#{@script_dir}/../opencvr-test/input"
    @ex_dir = "#{@script_dir}/../opencvr-test/expected"
    @out_dir = "#{@script_dir}/out"
    FileUtils.mkdir_p(@out_dir)
  end

  def test_version
    assert_equal(CV2::getVersionMajor.class, Integer)
    assert_equal(CV2::getVersionMinor.class, Integer)
    assert_equal(CV2::getVersionRevision.class, Integer)
    assert_equal(CV2::getVersionString.class, String)
  end

  def test_rectangle
    img0 = Numo::UInt8.zeros(400, 600, 3)
    img1 = img0.clone()
    CV2::rectangle(img1, [100,100], [200, 200], [255,0,0])
    CV2::rectangle(img1, [300,100, 100, 100], [0,0,255])
    assert_not_equal(img0, img1)
  end

  def test_putText
      img0 = Numo::UInt8.zeros(600, 800, 3)
      img0[0..-1, 0..-1, 0] = 255
      img1 = img0
      img2 = img0.clone()
      CV2::putText(img0, "Hello", [100, 100], CV2::FONT_HERSHEY_PLAIN, 5, [255,255,255], 2)
      CV2::rectangle(img0, [50,50], [150, 100], [255,255,255])
      assert_equal(img0, img1)
      assert_not_equal(img0, img2)
  end

  def test_hconcat # test of vector_Mat
    img0 = Numo::UInt8.zeros(200, 200, 3)
    img0[0..-1, 0..-1, 0] = 255
    img1 = Numo::UInt8.zeros(200, 200, 3)
    img1[0..-1, 0..-1, 1] = 255
    img2 = CV2::hconcat([img0, img1])
    assert_equal(img2.shape, [200, 400, 3])
  end

  def test_findContours1
    img_c = CV2.imread("#{@in_dir}/opencv-logo.png")
    img_c2 = img_c.clone()
    img_g = CV2.cvtColor(img_c2, CV2::COLOR_BGR2GRAY)
    contours, hierarchy = CV2.findContours(img_g, CV2::RETR_TREE, CV2::CHAIN_APPROX_SIMPLE)
    contours.each{|cnt|
      cnt.to_a.each{|pt|
        CV2.circle(img_c2, pt[0], 1, [0,0,255], 1)
      }
      center_f, radius_f = CV2.minEnclosingCircle(cnt)
      center_i = Numo::Int32.cast(center_f)
      radius_i = radius_f.to_i
      CV2.circle(img_c2, center_i.to_a, radius_i, [255,0,0])
    }
    CV2::imwrite("#{@out_dir}/findContours1.png", img_c2)
    assert_equal(CV2.imread("#{@out_dir}/findContours1.png"), CV2.imread("#{@ex_dir}/findContours1.png"))
  end

  def test_aruco1
    dict = CV2::Aruco.getPredefinedDictionary(CV2::Aruco::DICT_6X6_250)
    marker = Numo::UInt8.zeros(200, 200, 1)
    marker = CV2::Aruco.generateImageMarker(dict, 23, 200, 1)
    CV2.imwrite("#{@out_dir}/aruco-marker23.png", marker)
    assert_equal(CV2.imread("#{@out_dir}/aruco-marker23.png"), CV2.imread("#{@ex_dir}/aruco-marker23.png"))
  end

  def test_aruco2
    img = CV2.imread("#{@in_dir}/singlemarkersoriginal.jpg")
    params = CV2::Aruco::DetectorParameters.new()
    dict = CV2::Aruco.getPredefinedDictionary(CV2::Aruco::DICT_6X6_250)
    detector = CV2::Aruco::ArucoDetector.new(dict, params)
    corners, ids, rejectedImgPoints = detector.detectMarkers(img)
    out_img = img.clone()
    CV2::Aruco.drawDetectedMarkers(out_img, corners, ids)
    CV2.imwrite("#{@out_dir}/out-aruco2.jpg", out_img)
    assert_equal(CV2.imread("#{@ex_dir}/out-aruco2.jpg"), CV2.imread("#{@out_dir}/out-aruco2.jpg"))
  end

  def test_threshold
    img = CV2.imread("../cvimage/sudoku.png", CV2::IMREAD_GRAYSCALE)
    ret, out_img1 = CV2.threshold(img, 50, 255, CV2::THRESH_BINARY)
    CV2.imwrite("#{@out_dir}/out-thresh1.jpg", out_img1)
    assert_equal(CV2.imread("#{@ex_dir}/out-thresh1.jpg"), CV2.imread("#{@out_dir}/out-thresh1.jpg"))
    ret, out_img2 = CV2.threshold(img, 50, 255, CV2::THRESH_BINARY + CV2::THRESH_OTSU)
    CV2.imwrite("#{@out_dir}/out-thresh2.jpg", out_img2)
    assert_equal(CV2.imread("#{@ex_dir}/out-thresh2.jpg"), CV2.imread("#{@out_dir}/out-thresh2.jpg"))
    out_img3 = CV2.adaptiveThreshold(img, 255, CV2::ADAPTIVE_THRESH_GAUSSIAN_C, CV2::THRESH_BINARY, 51, 20)
    CV2.imwrite("#{@out_dir}/out-thresh3.jpg", out_img3)
    assert_equal(CV2.imread("#{@ex_dir}/out-thresh3.jpg"), CV2.imread("#{@out_dir}/out-thresh3.jpg"))
  end

  def test_orb1
    orb = CV2::ORB::create()
    assert_equal("Feature2D.ORB", orb.getDefaultName())
    assert_equal(31, orb.getPatchSize())
    assert_equal(32, orb.descriptorSize())
  end
end
