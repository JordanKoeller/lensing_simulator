package main

import java.io._

import org.apache.spark.api.java.JavaRDD

import lensing.RayParameters
import lensing.RayTracer
import spatialrdd.GridGenerator
import spatialrdd.RDDGrid
import spatialrdd.RDDGridProperty
//import spatialrdd.XYIntPair
import spatialrdd.partitioners.BalancedColumnPartitioner


object Main extends App {

  private var rddGrid: RDDGridProperty = null
  private var filename: String = "/tmp/lenssim_tmpfile"

  def setFile(fname: String) = filename = fname

  def createRDDGrid(
    starsfile: String,
    pointConstant: Double,
    sisConstant: Double,
    shearMag: Double,
    shearAngle: Double,
    dTheta: Double,
    centerX: Double,
    centerY: Double,
    width: Int,
    height: Int,
    ctx: JavaRDD[Int],
    partitionCount: Int): Unit = {
    if (rddGrid != null) rddGrid.destroy()
    println("Doing the full calculation")
    val sc = ctx.context
    sc.setLogLevel("WARN")
    val stars = scala.io.Source.fromFile(starsfile).getLines().toArray.map { row =>
      val starInfoArr = row.split(",").map(_.toDouble)
      (starInfoArr(0), starInfoArr(1), starInfoArr(2))
    }
    //Construction of RDD, mapping of RDD to ray-traced source plane locations
    val rayTracer = new RayTracer()
    val pixels = sc.range(0, (width * height).toLong, 1, partitionCount)
    val parameters = RayParameters(
      stars,
      pointConstant,
      sisConstant,
      shearMag,
      shearAngle,
      dTheta,
      centerX,
      centerY,
      width.toDouble,
      height.toDouble)

    val broadParams = sc.broadcast(parameters)
    val mappedPixels = rayTracer(pixels, broadParams)
    //Now need to construct the grid
    // val partitioner = new ColumnPartitioner()
    val partitioner = new BalancedColumnPartitioner

    rddGrid = RDDGrid(mappedPixels, partitioner)
    broadParams.unpersist()
  }

  def query_single_point(
    starsfile: String,
    pointConstant: Double,
    sisConstant: Double,
    shearMag: Double,
    shearAngle: Double,
    dTheta: Double,
    centerX: Double,
    centerY: Double,
    width: Int,
    height: Int,
    ctx: JavaRDD[Int],
    partitionCount: Int,
    qptx:Double,
    qpty:Double,
    radius:Double): Long = {
    println("Querying a single point")
    val sc = ctx.context
    sc.setLogLevel("WARN")
    val stars = scala.io.Source.fromFile(starsfile).getLines().toArray.map { row =>
      val starInfoArr = row.split(",").map(_.toDouble)
      (starInfoArr(0), starInfoArr(1), starInfoArr(2))
    }
    //Construction of RDD, mapping of RDD to ray-traced source plane locations
    val rayTracer = new RayTracer()
    val pixels = sc.range(0, (width * height).toLong, 1, partitionCount)
    val parameters = RayParameters(
      stars,
      pointConstant,
      sisConstant,
      shearMag,
      shearAngle,
      dTheta,
      centerX,
      centerY,
      width.toDouble,
      height.toDouble)

    val broadParams = sc.broadcast(parameters)
    val mappedPixels = rayTracer(pixels, broadParams)
    val r2 = radius*radius
    val pts = mappedPixels.filter{ray =>
      val dx = ray._1 - qptx
      val dy = ray._2 - qpty
      dx*dx+dy*dy <= r2
    }
    val ret = pts.count()
    broadParams.unpersist()
    ret
  }

  def rddFromFile(fname: String, numPartitions: Int, ctx: JavaRDD[Int]) = {
    println("Loading in form file " + fname)
    val sc = ctx.sparkContext
    rddGrid = RDDGrid.fromFile(fname, numPartitions, sc)
    println("Done")
  }

  def storeRDDFile(fname: String) = {
    if (rddGrid != null) rddGrid.saveToFile(fname)
    println("Stored into file " + fname) 
  }

  def queryPoints(x0: Double, y0: Double, x1: Double, y1: Double, xDim: Int, yDim: Int, radius: Double, ctx: JavaRDD[Int], verbose: Boolean = false) = {
    val sc = ctx.context
    val generator = new GridGenerator(x0, y0, x1, y1, xDim, yDim)
    val retArr = rddGrid.queryPointsFromGen(generator, radius, sc, verbose = verbose)
    writeFile(retArr)
  }

  def sampleLightCurves(filename: String, radius: Double, ctx: JavaRDD[Int]) {
    val sc = ctx.context
    val lightCurves = scala.io.Source.fromFile(filename).getLines().toArray.map { row =>
      val queryLine = row.split(",").map { elem =>
        val pair = elem.split(":").map(_.toDouble)
        (pair.head, pair.last)
      }
      queryLine
    }
    val retArr = rddGrid.queryPoints(lightCurves, radius, sc, false)
    writeFile(retArr)

  }

  def querySingleCurve(fname: String, radius: Double, ctx: JavaRDD[Int]) {
    val sc = ctx.context
    val lightCurves = scala.io.Source.fromFile(fname).getLines().toArray.map { elem =>
      val pair = elem.split(",").map(_.toDouble)
      (pair.head, pair.last)
    }
    val retArr = rddGrid.query_curve(lightCurves, radius, sc)
    val writer = new PrintWriter(new File(filename))
    val dString = retArr.mkString("\n")
    writer.write(dString)
    writer.close()
  }

  private def writeFile(data: Array[Array[Int]]): Unit = {
    val writer = new PrintWriter(new File(filename))
    val dString = data.map(_.mkString(",")).mkString(":")
    writer.write(dString)
    writer.close()
  }
}
